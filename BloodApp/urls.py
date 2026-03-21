from django.urls import path

from . import views

urlpatterns = [path("index.html", views.index, name="index"),
	             path("HospitalLogin.html", views.HospitalLogin, name="HospitalLogin"),
		     path("HospitalLoginAction", views.HospitalLoginAction, name="HospitalLoginAction"),
		     path("BankLogin.html", views.BankLogin, name="BankLogin"),
		     path("BankLoginAction", views.BankLoginAction, name="BankLoginAction"),
		     path("DonorLogin.html", views.DonorLogin, name="DonorLogin"),
		     path("DonorLoginAction", views.DonorLoginAction, name="DonorLoginAction"),
		     path("PatientLogin.html", views.PatientLogin, name="PatientLogin"),
		     path("PatientLoginAction", views.PatientLoginAction, name="PatientLoginAction"),

		     path("SearchBlood.html", views.SearchBlood, name="SearchBlood"),
		     path("SearchBloodAction", views.SearchBloodAction, name="SearchBloodAction"),

		     path("PatientSearch.html", views.PatientSearch, name="PatientSearch"),
		     path("PatientSearchAction", views.PatientSearchAction, name="PatientSearchAction"),
		     path("ViewDonation", views.ViewDonation, name="ViewDonation"),

		     path("Forecast.html", views.Forecast, name="Forecast"),
		     path("ForecastAction", views.ForecastAction, name="ForecastAction"),
		     path("Optimize", views.Optimize, name="Optimize"),

		     path("DonationDrive.html", views.DonationDrive, name="DonationDrive"),
		     path("DonationDriveAction", views.DonationDriveAction, name="DonationDriveAction"),
		     path("ReleaseBlood.html", views.ReleaseBlood, name="ReleaseBlood"),
		     path("ReleaseBloodAction", views.ReleaseBloodAction, name="ReleaseBloodAction"),
		     path("Register.html", views.Register, name="Register"),
		     path("RegisterAction", views.RegisterAction, name="RegisterAction"),
		     
		      ]