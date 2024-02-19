from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView, ListView, UpdateView, DeleteView, DetailView
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from guardian.mixins import LoginRequiredMixin
from django.http import JsonResponse
from collections import defaultdict


from bhtom2.bhtom_observatory.forms import ObservatoryCreationForm, ObservatoryUpdateForm, ObservatoryUserUpdateForm, \
    ObservatoryUserCreationForm, CamerasFormSet, CamerasUpdateFormSet
from bhtom2.bhtom_observatory.models import Observatory, ObservatoryMatrix, Camera
from bhtom2.utils.bhtom_logger import BHTOMLogger

logger: BHTOMLogger = BHTOMLogger(__name__, 'Bhtom: bhtom_observatory.views')


class CreateObservatory(LoginRequiredMixin, FormView):
    template_name = 'bhtom_observatory/observatory_create.html'
    form_class = ObservatoryCreationForm
    success_url = reverse_lazy('bhtom_observatory:list')
    def get_context_data(self, **kwargs):
        """
        Inserts certain form data into the context dict.

        :returns: Dictionary with the following keys:

                  `type_choices`: ``tuple``: Tuple of 2-tuples of strings containing available target types in the TOM

                  `extra_form`: ``FormSet``: Django formset with fields for arbitrary key/value pairs
        :rtype: dict
        """
        context = super(CreateObservatory, self).get_context_data(**kwargs)
        context['cameras'] = CamerasFormSet()
        return context
    
    def post(self, request, *args, **kwargs):
        form = self.get_form()
        cameras = CamerasFormSet(request.POST, request.FILES)
        
        if form.is_valid() and cameras.is_valid():
            return self.form_valid(form, cameras)
        else:
            return self.form_invalid(form, cameras)

    def form_valid(self, form, cameras):
        cameras = CamerasFormSet(self.request.POST,self.request.FILES)

        try:
            active_flag = False
            if form.cleaned_data['calibration_flg'] != True:
                user = self.request.user
                name = form.cleaned_data['name']
                lon = form.cleaned_data['lon']
                lat = form.cleaned_data['lat']
                calibration_flg = form.cleaned_data['calibration_flg']
                altitude = form.cleaned_data['altitude']
                approx_lim_mag = form.cleaned_data['approx_lim_mag']
                filters = form.cleaned_data['filters']
                comment = form.cleaned_data['comment']
            else:
                user = self.request.user
                name = form.cleaned_data['name']
                lon = form.cleaned_data['lon']
                lat = form.cleaned_data['lat']
                calibration_flg = form.cleaned_data['calibration_flg']
                altitude = None
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
                user=user,
                altitude=altitude,
                approx_lim_mag=approx_lim_mag,
                filters=filters,
                comment=comment
            )

            if cameras.is_valid():
                super().form_valid(form)
                observatory.save()
                cameras.instance = observatory
                cameras.save()
            logger.info('Create new obserwatory and camera:  %s' % str(name))
          
        except Exception as e:
            logger.error('CreateObservatory error: ' + str(e))
            messages.error(self.request, 'Error with creating the observatory or camera')
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
    
    def form_invalid(self, form, cameras):
        return self.render_to_response(self.get_context_data(form=form, cameras=cameras))

class ObservatoryList(LoginRequiredMixin, ListView):
    template_name = 'bhtom_observatory/observatory_list.html'
    model = Observatory
    strict = False

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        userObservatory = ObservatoryMatrix.objects.filter(user=self.request.user).order_by('observatory__name')

        observatory_user_dict = defaultdict(list)
        for row in userObservatory:
            observatory_user_dict[row.observatory.name].append(
                [row.id, row.active_flg, row.comment, Observatory.objects.get(id=row.observatory.id)])

        observatory_user_list = []
        for name, observatories in observatory_user_dict.items():
            observatory_user_list.append(observatories[0])  # Add only the first observatory with the same name

        context['observatory_list'] = Observatory.objects.filter(active_flg=True).order_by('name')
        context['observatory_user_list'] = observatory_user_list

        return context


class UpdateObservatory(LoginRequiredMixin, UpdateView):
    template_name = 'bhtom_observatory/observatory_create.html'
    form_class = ObservatoryUpdateForm
    success_url = reverse_lazy('bhtom_observatory:list')
    model = Observatory

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['cameras'] = CamerasUpdateFormSet(self.request.POST, self.request.FILES, instance=self.object)
        else:
            context['cameras'] = CamerasUpdateFormSet(instance=self.object)
        return context
    
    @transaction.atomic
    def form_valid(self, form):
        context = self.get_context_data()
        cameras = context['cameras']
        if cameras.is_valid():
            self.object = form.save()  # Save the observatory instance
            cameras.instance = self.object  # Associate cameras with the observatory
            cameras.save()  # Save cameras
            messages.success(self.request, 'Successfully updated %s' % form.cleaned_data['name'])
            logger.info("Update observatory %s, user: %s" % (str(form.instance), str(self.request.user)))
            return super().form_valid(form)
        else:
            logger.error(cameras.errors)
            cameras_errors = "\n".join([", ".join(errors) for errors in cameras.errors])
            messages.error(self.request, f'Failed to update {form.cleaned_data["name"]}. Cameras errors: {cameras_errors}')
            return self.render_to_response(self.get_context_data(form=form))
        


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        observatory = self.get_object()
        cameras = Camera.objects.filter(observatory=observatory)
        context['cameras'] = cameras
        return context
    

 
class ObservatoryFavoriteDetailView(LoginRequiredMixin, DetailView):
    model = Observatory
    template_name = 'bhtom_observatory/observatory_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        observatory = self.get_object()
        user = self.request.user
        obsMatrix = ObservatoryMatrix.objects.filter(observatory=observatory, user=user)
        
        camera_ids = [obs.camera.id for obs in obsMatrix]
        cameras = Camera.objects.filter(observatory=observatory, id__in=camera_ids)
        
        context['cameras'] = cameras
        return context

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
        camera = form.cleaned_data['camera']
        comment = form.cleaned_data['comment']

        if not observatoryId.active_flg:
            logger.error('observatory is not active')
            messages.error(self.request, 'Error with creating the user observatory')
            return redirect(self.get_success_url())

        try:
            observatoryUser = ObservatoryMatrix.objects.create(
                user=user,
                observatory= observatoryId,
                camera=camera,
                active_flg=True,
                comment=comment
            )
            observatoryUser.save()

            logger.info('Create user observatory: %s camera: %s, %s' % (observatoryId.name  ,camera.camera_name, str(user)))

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



def get_cameras(request, observatory_id, user_id):
    try:
        cameras = ObservatoryMatrix.objects.filter(user=user_id)
        insTab = [ins.camera.id for ins in cameras]  
        observatory_id = int(observatory_id)
        cameras = Camera.objects.exclude(id__in=insTab).filter(observatory_id=observatory_id).values('id', 'camera_name')
        return JsonResponse(list(cameras), safe=False)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid observatory ID'}, status=400)
    


def get_favorite_cameras(request, observatory_id, user_id):
    try:
        obsMatrix = ObservatoryMatrix.objects.filter(user=user_id, observatory=observatory_id)
        favorite_camera_ids = [obs.camera.id for obs in obsMatrix]
        favorite_cameras = Camera.objects.filter(id__in=favorite_camera_ids).values('id', 'camera_name')
        return JsonResponse(list(favorite_cameras), safe=False)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid observatory or user ID'}, status=400)