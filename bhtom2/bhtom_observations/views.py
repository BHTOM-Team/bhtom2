from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from guardian.shortcuts import get_objects_for_user

from bhtom_base.bhtom_observations.models import Proposal


class ProposalListView(LoginRequiredMixin, ListView):
    template_name = 'bhtom_observations/proposal_list.html'
    strict = False
    model = Proposal

    def get_queryset(self):
        if self.request.user.has_perm('bhtom_observations.view_proposal'):
            return Proposal.objects.all()
        else:
            return get_objects_for_user(self.request.user, Proposal)
