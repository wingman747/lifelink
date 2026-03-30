from django.urls import path
from . import views

urlpatterns = [
    # Home & Index
    path('', views.index, name='index'),
    
    # Hospital Login
    path('HospitalLogin/', views.HospitalLogin, name='HospitalLogin'),
    path('HospitalLogin/action/', views.HospitalLoginAction, name='HospitalLoginAction'),
    
    # Blood Bank Login
    path('BankLogin/', views.BankLogin, name='BankLogin'),
    path('BankLogin/action/', views.BankLoginAction, name='BankLoginAction'),
    
    # Donor Login
    path('DonorLogin/', views.DonorLogin, name='DonorLogin'),
    path('DonorLogin/action/', views.DonorLoginAction, name='DonorLoginAction'),
    
    # Patient Login
    path('PatientLogin/', views.PatientLogin, name='PatientLogin'),
    path('PatientLogin/action/', views.PatientLoginAction, name='PatientLoginAction'),
    


    # Hospital Enhancements
    path('HospitalDashboard/', views.HospitalDashboard, name='HospitalDashboard'),
    path('RequestBlood/', views.RequestBlood, name='RequestBlood'),
    path('RequestBlood/action/', views.RequestBloodAction, name='RequestBloodAction'),
    path('ViewBloodRequests/', views.ViewBloodRequests, name='ViewBloodRequests'),
    path('AddPatient/', views.AddPatient, name='AddPatient'),
    path('AddPatient/action/', views.AddPatientAction, name='AddPatientAction'),
    path('ViewPatients/', views.ViewPatients, name='ViewPatients'),
    path('ViewHospitalInventory/', views.ViewHospitalInventory, name='ViewHospitalInventory'),
    
    # User Registration
    path('Register/', views.Register, name='Register'),
    path('Register/action/', views.RegisterAction, name='RegisterAction'),
    
    # Blood Search
    path('SearchBlood/', views.SearchBlood, name='SearchBlood'),
    path('SearchBlood/action/', views.SearchBloodAction, name='SearchBloodAction'),
    
    # Patient Search
    path('PatientSearch/', views.PatientSearch, name='PatientSearch'),
    path('PatientSearch/action/', views.PatientSearchAction, name='PatientSearchAction'),
    
    # View Donations
    path('ViewDonation/', views.ViewDonation, name='ViewDonation'),
    
    # Forecasting
    path('Forecast/', views.Forecast, name='Forecast'),
    path('Forecast/action/', views.ForecastAction, name='ForecastAction'),
    
    # Donor Optimization
    path('Optimize/', views.Optimize, name='Optimize'),
    
    # Donation Drive
    path('DonationDrive/', views.DonationDrive, name='DonationDrive'),
    path('DonationDrive/action/', views.DonationDriveAction, name='DonationDriveAction'),
    
    # Release Blood
    path('ReleaseBlood/', views.ReleaseBlood, name='ReleaseBlood'),
    path('ReleaseBlood/action/', views.ReleaseBloodAction, name='ReleaseBloodAction'),
    
    # Inventory Management
    path('ViewInventory/', views.ViewInventory, name='ViewInventory'),
    path('UpdateInventoryForm/', views.UpdateInventoryForm, name='UpdateInventoryForm'),
    path('UpdateInventory/action/', views.UpdateInventoryAction, name='UpdateInventoryAction'),
    
    # Blood Expiry Tracker
    path('BloodExpiryTracker/', views.BloodExpiryTracker, name='BloodExpiryTracker'),
    
    # ============= ADMIN ROUTES =============
    path('AdminLogin/', views.AdminLogin, name='AdminLogin'),
    path('AdminLogin/action/', views.AdminLoginAction, name='AdminLoginAction'),
    path('AdminDashboard/', views.AdminDashboard, name='AdminDashboard'),
    path('AdminViewUsers/', views.AdminViewUsers, name='AdminViewUsers'),
    path('AdminDeleteUser/', views.AdminDeleteUser, name='AdminDeleteUser'),
    path('AdminViewDonations/', views.AdminViewDonations, name='AdminViewDonations'),
    path('AdminViewBloodBanks/', views.AdminViewBloodBanks, name='AdminViewBloodBanks'),
    path('AdminSystemReports/', views.AdminSystemReports, name='AdminSystemReports'),
    path('AdminActivityLog/', views.AdminActivityLog, name='AdminActivityLog'),
    path('AdminLogout/', views.AdminLogout, name='AdminLogout'),
    
    # ============= INSTITUTION AUTH ROUTES =============
    path('register/institution/', views.register_institution_user, name='institution_register'),
    path('institution/not-verified/', views.institution_not_verified, name='institution_not_verified'),
    path('account/disabled/', views.account_disabled, name='account_disabled'),
    
    # ============= NEW ADMIN ROUTES =============
    path('admin/users/', views.AdminViewUsers, name='admin_view_users'),
    path('admin/institutions/', views.AdminViewInstitutions, name='admin_view_institutions'),
    path('admin/institution-users/', views.AdminViewInstitutionUsers, name='admin_view_institution_users'),

    path('Register/', views.Register, name='Register'),
    path('Register/action/', views.RegisterAction, name='RegisterAction'),
    path('BloodBankMap/', views.PublicBloodBankMap, name='PublicBloodBankMap'),  # ✅ Add "Public" prefix
    path('FindNearestBloodBank/', views.PublicFindNearestBloodBank, name='PublicFindNearestBloodBank'),
    path('BloodBankDirectory/', views.PublicBloodBankDirectory, name='PublicBloodBankDirectory'),

    # Add these lines to your urlpatterns list

    # Blood Bank URLs
    path('blood-bank/dashboard/', views.blood_bank_dashboard, name='blood_bank_dashboard'),
    path('blood-request/<int:request_id>/', views.view_blood_request, name='view_blood_request'),
    path('blood-request/<int:request_id>/approve/', views.approve_blood_request, name='approve_blood_request'),
    path('blood-request/<int:request_id>/fulfill/', views.fulfill_blood_request, name='fulfill_blood_request'),
    path('blood-request/<int:request_id>/reject/', views.reject_blood_request, name='reject_blood_request'),
    path('blood-requests/json/', views.get_blood_requests_json, name='get_blood_requests_json'),

    # Hospital URLs
    path('hospital/request-blood/', views.request_blood, name='request_blood'),
    path('hospital/blood-requests/', views.hospital_blood_requests, name='hospital_blood_requests'),
    path('hospital/blood-request/<int:request_id>/', views.hospital_view_request, name='hospital_view_request'),
]