from django import forms

from bhtom_base.bhtom_dataproducts.models import DataProduct


class UpdateFitsForm(forms.ModelForm):

    status_message = forms.CharField(
        label='Status Message', required=False,
        widget=forms.Textarea(attrs={'rows': 1, 'cols': 200}),
    )

    delete_fits = forms.BooleanField(
        label='Delete Fits from disk', required=False,
        initial=False,
    )

    def __init__(self, *args, **kwargs):
        super(UpdateFitsForm, self).__init__(*args, **kwargs)

    class Meta:
        model = DataProduct
        fields = ('status', 'status_message', 'delete_fits')
