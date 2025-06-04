from django import forms
from django.forms import modelformset_factory
from .models import SpecializationPrice

class SpecializationPriceForm(forms.ModelForm):
    class Meta:
        model = SpecializationPrice
        fields = ['specialization', 'price']
        widgets = {
            'specialization': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={
    'class': 'form-control bg-white shadow-sm form-control-sm price-input',
    'style': 'height: 38px; padding: 6px 12px; margin:0; resize: none;'
}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk and self.instance.price is not None:
            decimal_price = f"{self.instance.price / 100:.2f}"
            self.fields['price'].initial = decimal_price

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is None:
            return price

        # Multiply by 100 to convert decimal to integer cents
        # You can also round it to avoid float precision issues
        price_cents = int(round(price * 100))
        return price_cents

SpecializationPriceFormSet = modelformset_factory(
    SpecializationPrice,
    form=SpecializationPriceForm,
    extra=0
)