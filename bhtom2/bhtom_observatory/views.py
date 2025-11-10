from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.views.generic import FormView, ListView, UpdateView, DeleteView, DetailView
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from guardian.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.db.models import Prefetch

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
    
    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        if not form.is_valid():
            cameras_formset = CamerasFormSet(self.request.POST, self.request.FILES, instance=form.instance)
            context['cameras'] = cameras_formset
        return self.render_to_response(context)
    
    def form_valid(self, form):
        cameras = CamerasFormSet(self.request.POST,self.request.FILES)
        try:
            if form.cleaned_data['calibration_flg'] != True:
                cameras.forms[0].empty_permitted = False
                user = self.request.user
                name = form.cleaned_data['name']
                lon = form.cleaned_data['lon']
                lat = form.cleaned_data['lat']
                calibration_flg = form.cleaned_data['calibration_flg']
                altitude = form.cleaned_data['altitude']
                approx_lim_mag = form.cleaned_data['approx_lim_mag']
                filters = form.cleaned_data['filters']
                comment = form.cleaned_data['comment']
                aperture = form.cleaned_data['aperture']
                focal_length = form.cleaned_data['focal_length']
                telescope = form.cleaned_data['telescope']
                authors = form.cleaned_data['authors']
                acknowledgements =  form.cleaned_data['acknowledgements']
            else:
                cameras.forms[0].empty_permitted = True
                user = self.request.user
                name = form.cleaned_data['name']
                lon = form.cleaned_data['lon']
                lat = form.cleaned_data['lat']
                calibration_flg = form.cleaned_data['calibration_flg']
                altitude = form.cleaned_data['altitude']
                approx_lim_mag = form.cleaned_data['approx_lim_mag']
                filters = form.cleaned_data['filters']
                comment = form.cleaned_data['comment']
                aperture = form.cleaned_data['aperture']
                focal_length = form.cleaned_data['focal_length']
                telescope = form.cleaned_data['telescope']
                authors = form.cleaned_data['authors']
                acknowledgements =  form.cleaned_data['acknowledgements']

        except TypeError as e:
            logger.error('CreateObservatory error: ' + str(e))
            messages.error(self.request, 'Error with creating the observatory')
            return redirect(self.get_success_url())

        try:
            observatory = Observatory.objects.create(
                name=name,
                lon=lon,
                lat=lat,
                calibration_flg=calibration_flg,
                user=user,
                altitude=altitude,
                approx_lim_mag=approx_lim_mag,
                filters=filters,
                comment=comment,
                aperture=aperture,
                focal_length=focal_length,
                telescope=telescope,
                authors=authors,
                acknowledgements=acknowledgements
            )
            if form.cleaned_data['calibration_flg'] != True:   
                if cameras.is_valid():
                    super().form_valid(form)
                    observatory.save()
                    cameras.instance = observatory
                    for camera_form in cameras:
                        camera = camera_form.save(commit=False)
                        camera.observatory = observatory       
                        camera.prefix = observatory.name + '_' + camera.camera_name               
                        camera.user = user                   
                        camera.save()
            else:
                super().form_valid(form)
                observatory.save()
                camera = Camera(observatory=observatory, user=user, camera_name="Only instrumental photometry file camera",active_flg= True)
                camera.active_flg= True
                camera.prefix = observatory.name + '_' + camera.camera_name             
                camera.save()

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



class ObservatoryList(LoginRequiredMixin, ListView):
    template_name = 'bhtom_observatory/observatory_list.html'
    model = Observatory

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)


        active_obs_id = Camera.objects.filter(active_flg=True).values_list("observatory_id", flat=True)

        observatories_with_active_cameras = Observatory.objects.filter(id__in=active_obs_id)

        # Initialize the dictionary to store observatory prefixes
        prefix_obs = {}

        # Iterate over observatories with active cameras
        for observatory in observatories_with_active_cameras:
            # Count the number of cameras in the observatory
            camera_count = Camera.objects.filter(observatory=observatory).count()

            # If there's only one camera, include its prefix
            if camera_count == 1:
                camera = Camera.objects.get(observatory=observatory)
                prefix_obs[observatory.id] = [camera.prefix]
            else:
                cameras = Camera.objects.filter(observatory=observatory)
                onames = [camera.prefix for camera in cameras]
                prefix_obs[observatory.id] = onames

        context['observatory_list'] = observatories_with_active_cameras
        context['prefix_obs'] = prefix_obs


        prefix_user_obs = {}

        user_cameras = ObservatoryMatrix.objects.filter(user=self.request.user).values_list('camera__id', flat=True)
        user_active_obs_id = Camera.objects.filter(id__in=user_cameras, active_flg=True).values_list('observatory_id',flat=True)
        user_observatories = Observatory.objects.filter(id__in=user_active_obs_id)

        for obs in user_observatories:
            camera_count = ObservatoryMatrix.objects.filter(user=self.request.user, camera__observatory= obs).count()
            if camera_count == 1:
                obsMatrix = ObservatoryMatrix.objects.get(user=self.request.user, camera__observatory= obs)
                prefix_user_obs[obs.id] = [obsMatrix.camera.prefix]
            else:
                obsMatrix = ObservatoryMatrix.objects.filter(user=self.request.user, camera__observatory= obs)
                onames = [obs.camera.prefix for obs in obsMatrix]
                prefix_user_obs[obs.id] = onames
        context['prefix_user_obs'] = prefix_user_obs
        context['observatory_user_list'] = user_observatories

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
        user = self.request.user
        if cameras.is_valid():
            super().form_valid(form)
            cameras.instance = self.object
            for camera_form in cameras:
                camera = camera_form.save(commit=False)
                camera.observatory = self.object          
                camera.prefix = self.object.name + camera.camera_name                    
                camera.user = user                       
                camera.save()

            messages.success(self.request, 'Successfully updated %s' % form.cleaned_data['name'])
            logger.info("Update observatory %s, user: %s" % (str(form.instance), str(self.request.user)))
            return super().form_valid(form)
        else:
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
        cameras = Camera.objects.filter(observatory=observatory, active_flg=True)
        context['cameras'] = cameras
        return context
    

 
class ObservatoryFavoriteDetailView(LoginRequiredMixin, DetailView):
    model = Observatory
    template_name = 'bhtom_observatory/userObservatory_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        observatory = self.get_object()
        user = self.request.user
        obsMatrix = ObservatoryMatrix.objects.filter(user=user,active_flg=True, camera__observatory=observatory)
        context['obsMatrix'] = obsMatrix
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

        try:
            observatoryUser = ObservatoryMatrix.objects.create(
                user=user,
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
        messages.success(self.request, 'Successfully deleted')
        logger.info("Delete observatory %s, user: %s" % (str(self.request), str(self.request.user)))
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
        logger.info('Update user observatory, %s, %s' % (str(form.instance.camera), str(self.request.user)))
        return redirect(self.get_success_url())


def get_cameras(request, observatory_id, user_id):
    try:
        user_cameras = ObservatoryMatrix.objects.filter(user=user_id).values_list('camera__id', flat=True)
        observatory_id = int(observatory_id)
        cameras = Camera.objects.exclude(id__in=user_cameras).filter(observatory_id=observatory_id,  active_flg=True).values('id', 'camera_name').order_by('camera_name')
        
        return JsonResponse(list(cameras), safe=False)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid observatory ID'}, status=400)

def get_favorite_cameras(request, observatory_id, user_id):
    try:
        user_cameras = ObservatoryMatrix.objects.filter(user=user_id).values_list('camera__id', flat=True)
        observatory_id = int(observatory_id)
        favorite_cameras = Camera.objects.filter(id__in=user_cameras, observatory_id=observatory_id,  active_flg=True).values('id', 'camera_name').order_by('camera_name')
        return JsonResponse(list(favorite_cameras), safe=False)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid observatory or user ID'}, status=400)
    



class ObservatoryPublicDetailView(DetailView):
    model = Observatory
    template_name = 'bhtom_observatory/observatory_detail.html'

    def get_object(self, queryset=None):
        identifier = self.kwargs.get('identifier')
        if identifier.isdigit():
            return get_object_or_404(Observatory, id=int(identifier))
        else:
            return get_object_or_404(Observatory, name=identifier)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        observatory = self.object
        cameras = Camera.objects.filter(observatory=observatory, active_flg=True)
        context['cameras'] = cameras
        return context

class ObservatoryPublicList(ListView):
    template_name = 'bhtom_observatory/observatory_list_public.html'
    model = Observatory

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)


        active_obs_id = Camera.objects.filter(active_flg=True).values_list("observatory_id", flat=True)

        observatories_with_active_cameras = Observatory.objects.filter(id__in=active_obs_id)

        # Initialize the dictionary to store observatory prefixes
        prefix_obs = {}

        # Iterate over observatories with active cameras
        for observatory in observatories_with_active_cameras:
            # Count the number of cameras in the observatory
            camera_count = Camera.objects.filter(observatory=observatory).count()

            # If there's only one camera, include its prefix
            if camera_count == 1:
                camera = Camera.objects.get(observatory=observatory)
                prefix_obs[observatory.id] = [camera.prefix]
            else:
                cameras = Camera.objects.filter(observatory=observatory)
                onames = [camera.prefix for camera in cameras]
                prefix_obs[observatory.id] = onames

        context['observatory_list'] = observatories_with_active_cameras
        context['prefix_obs'] = prefix_obs
        return context
    