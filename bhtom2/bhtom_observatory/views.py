import logging

from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import FormView, ListView, UpdateView, DeleteView, DetailView
from django.contrib import messages

from guardian.mixins import LoginRequiredMixin

from bhtom2.bhtom_observatory.forms import ObservatoryCreationForm, ObservatoryUpdateForm, ObservatoryUserUpdateForm, \
    ObservatoryUserCreationForm
from bhtom2.bhtom_observatory.models import Observatory, ObservatoryMatrix

logger = logging.getLogger(__name__)


class CreateObservatory(LoginRequiredMixin, FormView):
    template_name = 'bhtom_observatory/observatory_create.html'
    form_class = ObservatoryCreationForm
    success_url = reverse_lazy('observatory:list')

    def form_valid(self, form):

        try:
            # super().form_valid(form)

            user = self.request.user
            name = form.cleaned_data['name']
            lon = form.cleaned_data['lon']
            lat = form.cleaned_data['lat']
            cpcsOnly = form.cleaned_data['cpcsOnly']

            example_file = self.request.FILES.get('fits')

            if cpcsOnly is True:
                prefix = name + "_CalibrationOnly"
            else:
                prefix = name

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

            if readout_speed is None:
                readout_speed = 9999.
            if pixel_size is None:
                pixel_size = 13.5

            observatory = Observatory.objects.create(
                name=name,
                lon=lon,
                lat=lat,
                isActive=False,
                prefix=prefix,
                cpcsOnly=cpcsOnly,
                example_file=example_file,
                user=user,
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
            logger.info('Send mail, create new obserwatory:  %s' % str(name))

        except Exception as e:
            logger.error('CreateObservatory error: ' + str(e))
            messages.error(self.request, 'Error with creating the observatory')
            return redirect(self.get_success_url())
        messages.success(self.request, 'Successfully created %s' % str(name))
        return redirect(self.get_success_url())


class ObservatoryList(LoginRequiredMixin, ListView):
    template_name = 'bhtom_observatory/observatory_list.html'
    model = Observatory
    strict = False

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        userObservatory = ObservatoryMatrix.objects.filter(user_id=self.request.user).order_by('observatory_id__name')

        observatory_user_list = []
        for row in userObservatory:
            observatory_user_list.append(
                [row.id, row.isActive, row.comment, Observatory.objects.get(id=row.observatory_id.id)])

        context['observatory_list'] = Observatory.objects.filter(isActive=True).order_by('name')
        context['observatory_user_list'] = observatory_user_list

        return context


class UpdateObservatory(LoginRequiredMixin, UpdateView):
    template_name = 'bhtom_observatory/observatory_create.html'
    form_class = ObservatoryUpdateForm
    success_url = reverse_lazy('observatory:list')
    model = Observatory

    @transaction.atomic
    def form_valid(self, form):
        super().form_valid(form)
        messages.success(self.request, 'Successfully updated %s' % form.cleaned_data['name'])
        return redirect(self.get_success_url())


class DeleteObservatory(LoginRequiredMixin, DeleteView):
    success_url = reverse_lazy('observatory:list')
    model = Observatory
    template_name = 'bhtom_observatory/observatory_delete.html'

    def get_object(self, queryset=None):
        obj = super(DeleteObservatory, self).get_object()
        return obj

    @transaction.atomic
    def form_valid(self, form):
        super().form_valid(form)
        messages.success(self.request, 'Successfully delete')
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
    success_url = reverse_lazy('observatory:list')

    def get_form_kwargs(self):
        kwargs = super(CreateUserObservatory, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):

        user = self.request.user
        observatoryID = form.cleaned_data['observatory']
        comment = form.cleaned_data['comment']
        observatoryUser = None

        try:
            observatoryUser = ObservatoryMatrix.objects.create(
                user_id=user,
                observatory_id=observatoryID,
                isActive=True,
                comment=comment
            )
            observatoryUser.save()

            logger.info('Send mail, %s, %s' % (observatoryID.name, str(user)))

        except Exception as e:
            logger.error('CreateInstrument error: ' + str(e))
            messages.error(self.request, 'Error with creating the instrument')
            observatoryUser.delete()
            return redirect(self.get_success_url())

        messages.success(self.request, 'Successfully created')
        return redirect(self.get_success_url())


class DeleteUserObservatory(LoginRequiredMixin, DeleteView):
    success_url = reverse_lazy('observatory:list')
    model = ObservatoryMatrix
    template_name = 'bhtom_observatory/userObservatory_delete.html'

    def get_object(self, queryset=None):
        obj = super(DeleteUserObservatory, self).get_object()
        return obj

    @transaction.atomic
    def form_valid(self, form):
        super().form_valid(form)
        messages.success(self.request, 'Successfully delete')
        return redirect(self.get_success_url())


class UpdateUserObservatory(LoginRequiredMixin, UpdateView):
    template_name = 'bhtom_observatory/userObservatory_create.html'
    form_class = ObservatoryUserUpdateForm
    success_url = reverse_lazy('observatory:list')
    model = ObservatoryMatrix

    @transaction.atomic
    def form_valid(self, form):
        super().form_valid(form)
        messages.success(self.request, 'Successfully updated')
        return redirect(self.get_success_url())

