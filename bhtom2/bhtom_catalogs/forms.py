from django import forms
from bhtom_base.bhtom_catalogs.harvester import get_service_classes

class CatalogQueryForm(forms.Form):
    """
    Form used for catalog harvesters ``CatalogQueryView``.
    """
    term = forms.CharField()
    service = forms.ChoiceField(choices=lambda: [(key, key) for key in get_service_classes().keys()])