from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView, ListView, UpdateView, DeleteView, DetailView
from django.contrib import messages

from django.conf import settings
from django.core.mail import send_mail
from guardian.mixins import LoginRequiredMixin

from bhtom2.bhtom_observatory.forms import ObservatoryCreationForm, ObservatoryUpdateForm, ObservatoryUserUpdateForm, \
    ObservatoryUserCreationForm
from bhtom2.bhtom_observatory.models import Observatory, ObservatoryMatrix
from bhtom2.utils.bhtom_logger import BHTOMLogger

logger: BHTOMLogger = BHTOMLogger(__name__, 'Bhtom: bhtom_observatory.views')


class CreateObservatory(LoginRequiredMixin, FormView):
    template_name = 'bhtom_observatory/observatory_create.html'
    form_class = ObservatoryCreationForm
    success_url = reverse_lazy('bhtom_observatory:list')

    def form_valid(self, form):

        try:
            active_flag = False
            if form.cleaned_data['calibration_flg'] != True:
                user = self.request.user
                name = form.cleaned_data['name']
                lon = form.cleaned_data['lon']
                lat = form.cleaned_data['lat']
                calibration_flg = form.cleaned_data['calibration_flg']
                example_file = self.request.FILES.get('fits')
                altitude = form.cleaned_data['altitude']
                gain = form.cleaned_data['gain']
                readout_noise = form.cleaned_data['readout_noise']
                binning = form.cleaned_data['binning']
                saturation_level = form.cleaned_data['saturation_level']
                pixel_scale = form.cleaned_data['pixel_scale']
                readout_speed = form.cleaned_data['readout_speed']
                pixel_size = form.cleaned_data['pixel_size']
                approx_lim_mag = form.cleaned_data['approx_lim_mag']
                filters = form.cleaned_data['filters']
                comment = form.cleaned_data['comment']
            else:
                user = self.request.user
                name = form.cleaned_data['name']
                lon = form.cleaned_data['lon']
                lat = form.cleaned_data['lat']
                calibration_flg = form.cleaned_data['calibration_flg']
                example_file = None
                altitude = None
                gain = None
                readout_noise = None
                binning = None
                saturation_level = None
                pixel_scale = None
                readout_speed = None
                pixel_size = None
                approx_lim_mag = None
                filters = None
                comment = None
                active_flag = True
                
            if calibration_flg is True:
                prefix = name + "_CalibrationOnly"
            else:
                prefix = name
        except TypeError as e:
            logger.error('CreateObservatory error: ' + str(e))
            messages.error(self.request, 'Error with creating the observatory')
            return redirect(self.get_success_url())

        try:
            observatory = Observatory.objects.create(
                name=name,
                lon=lon,
                lat=lat,
                active_flg=active_flag,
                prefix=prefix,
                calibration_flg=calibration_flg,
                example_file=example_file,
                user=user,
                altitude=altitude,
                gain=gain,
                readout_noise=readout_noise,
                binning=binning,
                saturation_level=saturation_level,
                pixel_scale=pixel_scale,
                readout_speed=readout_speed,
                pixel_size=pixel_size,
                approx_lim_mag=approx_lim_mag,
                filters=filters,
                comment=comment
            )

            observatory.save()
            logger.info('Create new obserwatory:  %s' % str(name))

        except Exception as e:
            logger.error('CreateObservatory error: ' + str(e))
            messages.error(self.request, 'Error with creating the observatory')
            return redirect(self.get_success_url())

      
        try:
            send_mail(settings.EMAILTEXT_CREATE_OBSERVATORY_TITLE,settings.EMAILTEXT_CREATE_OBSERVATORY, 
                  settings.EMAIL_HOST_USER, [user.email])

            send_mail(settings.EMAILTEXT_CREATE_OBSERVATORY_TITLE,settings.EMAILTEXT_CREATE_OBSERVATORY_ADMIN + str(user) + ', ' + observatory.name, 
                  settings.EMAIL_HOST_USER, settings.RECIPIENTEMAIL)
              logger.info('Send mail, %s, %s' % (observatory.name, str(user)))
        except Exception as e:
              logger.info('Error while sending mail, %s, %s' % (observatory.name, str(user)))


        messages.success(self.request, '%s successfully created, observatory requires administrator approval' % str(name))
        return redirect(self.get_success_url())


class ObservatoryList(LoginRequiredMixin, ListView):
    template_name = 'bhtom_observatory/observatory_list.html'
    model = Observatory
    strict = False

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        userObservatory = ObservatoryMatrix.objects.filter(user=self.request.user).order_by('observatory__name')

        observatory_user_list = []
        for row in userObservatory:
            observatory_user_list.append(
                [row.id, row.active_flg, row.comment, Observatory.objects.get(id=row.observatory.id)])

        context['observatory_list'] = Observatory.objects.filter(active_flg=True).order_by('name')
        context['observatory_user_list'] = observatory_user_list

        return context


class UpdateObservatory(LoginRequiredMixin, UpdateView):
    template_name = 'bhtom_observatory/observatory_create.html'
    form_class = ObservatoryUpdateForm
    success_url = reverse_lazy('bhtom_observatory:list')
    model = Observatory

    @transaction.atomic
    def form_valid(self, form):
        super().form_valid(form)
        messages.success(self.request, 'Successfully updated %s' % form.cleaned_data['name'])
        logger.info("Update observatory %s, user: %s" % (str(form.instance), str(self.request.user)))
        return redirect(self.get_success_url())


class DeleteObservatory(LoginRequiredMixin, DeleteView):
    success_url = reverse_lazy('bhtom_observatory:list')
    model = Observatory
    template_name = 'bhtom_observatory/observatory_delete.html'

    def get_object(self, queryset=None):
        obj = super(DeleteObservatory, self).get_object()
        return obj

    @transaction.atomic
    def form_valid(self, form):
        super().form_valid(form)
        messages.success(self.request, 'Successfully delete')
        logger.info("Delete observatory %s, user: %s" % (str(self.request), str(self.request.user)))
        return redirect(self.get_success_url())


class ObservatoryDetailView(LoginRequiredMixin, DetailView):
    model = Observatory
    template_name = 'bhtom_observatory/observatory_detail.html'

    # def get(self, request, *args, **kwargs):
    #     observatory_id = kwargs.get('pk', None)
    #     return redirect(reverse('observatory_detail', args=(observatory_id,)))


class CreateUserObservatory(LoginRequiredMixin, FormView):
    """
    View that handles manual upload of DataProducts. Requires authentication.
    """

    template_name = 'bhtom_observatory/userObservatory_create.html'
    form_class = ObservatoryUserCreationForm
    success_url = reverse_lazy('bhtom_observatory:list')

    def get_form_kwargs(self):
        kwargs = super(CreateUserObservatory, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):

        user = self.request.user
        observatoryId = form.cleaned_data['observatory']
        comment = form.cleaned_data['comment']

        if not observatoryId.active_flg:
            logger.error('observatory is not active')
            messages.error(self.request, 'Error with creating the user observatory')
            return redirect(self.get_success_url())

        try:
            observatoryUser = ObservatoryMatrix.objects.create(
                user=user,
                observatory=observatoryId,
                active_flg=True,
                comment=comment
            )
            observatoryUser.save()

            logger.info('Create user observatory, %s, %s' % (observatoryId.name, str(user)))

        except Exception as e:
            logger.error('Create user observatory error: ' + str(e))
            messages.error(self.request, 'Error with creating the user observatory')
            return redirect(self.get_success_url())

        messages.success(self.request, 'Successfully created')
        return redirect(self.get_success_url())


class DeleteUserObservatory(LoginRequiredMixin, DeleteView):
    success_url = reverse_lazy('bhtom_observatory:list')
    model = ObservatoryMatrix
    template_name = 'bhtom_observatory/userObservatory_delete.html'

    def get_object(self, queryset=None):
        obj = super(DeleteUserObservatory, self).get_object()
        return obj

    @transaction.atomic
    def form_valid(self, form):
        super().form_valid(form)
        messages.success(self.request, 'Successfully delete')
        logger.info('Delete user observatory, %s, %s' % (str(self.object), str(self.request.user)))
        return redirect(self.get_success_url())


class UpdateUserObservatory(LoginRequiredMixin, UpdateView):
    template_name = 'bhtom_observatory/userObservatory_create.html'
    form_class = ObservatoryUserUpdateForm
    success_url = reverse_lazy('bhtom_observatory:list')
    model = ObservatoryMatrix

    @transaction.atomic
    def form_valid(self, form):
        super().form_valid(form)
        messages.success(self.request, 'Successfully updated')
        logger.info('Update user observatory, %s, %s' % (str(form.instance.observatory), str(self.request.user)))
        return redirect(self.get_success_url())
