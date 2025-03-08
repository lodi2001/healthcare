from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User

class UserRegistrationForm(UserCreationForm):
    """
    Form for user registration with custom fields based on user type.
    """
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    national_id = forms.CharField(max_length=20, required=True)
    phone_number = forms.CharField(max_length=15, required=True)
    region = forms.CharField(max_length=100, required=True)
    city = forms.CharField(max_length=100, required=True)
    district = forms.CharField(max_length=100, required=True)
    terms_accepted = forms.BooleanField(required=True)
    
    # Fields for healthcare providers
    healthcare_provider_type = forms.ChoiceField(
        choices=User.HEALTHCARE_PROVIDER_TYPE_CHOICES,
        required=False
    )
    
    # Fields for companies
    company_name = forms.CharField(max_length=200, required=False)
    
    # Hidden field for hospital/clinic name (will be copied to first_name)
    hospital_name = forms.CharField(max_length=200, required=False)
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'national_id', 
                  'phone_number', 'region', 'city', 'district', 'terms_accepted',
                  'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        self.user_type = kwargs.pop('user_type', None)
        super().__init__(*args, **kwargs)
        
        # Set user_type field value
        if self.user_type:
            self.initial['user_type'] = self.user_type
            
        # Show/hide fields based on user type
        if self.user_type == 'healthcare_provider':
            self.fields['healthcare_provider_type'].required = True
        else:
            self.fields.pop('healthcare_provider_type', None)
            
        if self.user_type == 'company':
            self.fields['company_name'].required = True
        else:
            self.fields.pop('company_name', None)
    
    def clean(self):
        cleaned_data = super().clean()
        
        # If this is a healthcare provider registration
        if self.user_type == 'healthcare_provider':
            provider_type = cleaned_data.get('healthcare_provider_type')
            
            # If provider type is clinic, validate hospital name
            if provider_type == 'clinic':
                hospital_name = self.data.get('hospital_name')
                
                # If hospital name is provided, use it for first_name
                if hospital_name:
                    cleaned_data['first_name'] = hospital_name
                    cleaned_data['last_name'] = 'Hospital'  # Default last name for hospitals
                    
                    # Change the label for national_id to indicate it's a CRN
                    self.fields['national_id'].label = 'Commercial Registration Number (CRN)'
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = self.user_type
        
        if commit:
            user.save()
            
            # Create UserProfile if it doesn't exist
            from .models import UserProfile
            profile, created = UserProfile.objects.get_or_create(user=user)
            
            # Create UserProfile with company_name if applicable
            if self.user_type == 'company' and 'company_name' in self.cleaned_data:
                profile.company_name = self.cleaned_data['company_name']
                profile.save()
            
            # Store hospital/clinic metadata if applicable
            if self.user_type == 'healthcare_provider' and self.cleaned_data.get('healthcare_provider_type') == 'clinic':
                if not profile.metadata:
                    profile.metadata = {}
                profile.metadata['is_hospital'] = True
                profile.metadata['hospital_name'] = self.cleaned_data.get('first_name')
                profile.save()
                
        return user


class UserLoginForm(AuthenticationForm):
    """
    Form for user login.
    """
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class PatientRegistrationForm(forms.ModelForm):
    """
    Form for healthcare providers to register patients.
    National ID is the key identifier.
    """
    first_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    national_id = forms.CharField(
        max_length=20, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='National ID is required and must be unique'
    )
    phone_number = forms.CharField(
        max_length=15, 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    date_of_birth = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )
    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    region = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    city = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    district = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'national_id', 
                  'phone_number', 'date_of_birth', 'gender', 'region', 'city', 'district')
    
    def clean_national_id(self):
        """Validate that the national ID is unique"""
        national_id = self.cleaned_data.get('national_id')
        if User.objects.filter(national_id=national_id).exists():
            raise forms.ValidationError('A patient with this National ID already exists')
        return national_id
    
    def clean_email(self):
        """Validate that the email is unique"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('A patient with this email already exists')
        return email
    
    def save(self, commit=True):
        """
        Save the patient with a generated username and password
        based on their national ID
        """
        user = super().save(commit=False)
        
        # Set user type to patient
        user.user_type = 'patient'
        
        # Generate username based on national ID
        user.username = f"patient_{user.national_id}"
        
        # Generate a random password (patients can reset it later if needed)
        import uuid
        random_password = uuid.uuid4().hex[:8]
        user.set_password(random_password)
        
        if commit:
            user.save()
        
        # Store the generated password so it can be displayed to the provider
        self.generated_password = random_password
        
        return user
