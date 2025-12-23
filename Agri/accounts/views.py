# views.py - UPDATED with correct template paths
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth import get_user_model

from .models import OTP
from .utils import send_sms_otp

User = get_user_model()

def login_view(request):
    error = None

    if request.method == "POST":
        mobile = request.POST.get("contact_number")
        role = request.POST.get("role")
        login_type = request.POST.get("login_type")

        # Basic validation
        if not mobile or not role:
            return render(request, "accounts/login.html", {"error": "Mobile number and role are required"})

        try:
            user = User.objects.get(contact_number=mobile, role=role)
        except User.DoesNotExist:
            return render(request, "accounts/login.html", {"error": "User not found with this mobile number and role"})

        if login_type == "password":
            password = request.POST.get("password")
            if not password:
                return render(request, "accounts/login.html", {"error": "Password is required"})
            
            # Use custom authentication backend
            user = authenticate(request, username=mobile, password=password)
            if user is not None:
                login(request, user)
                
                # Redirect based on role
                if user.role == "admin":
                    return redirect("/admin/")
                elif user.role == "farmer":
                    return redirect("/farmer/dashboard/")
                elif user.role == "buyer":
                    return redirect("/buyer/dashboard/")
                else:
                    return redirect("/dashboard/")
            else:
                error = "Invalid password"

        elif login_type == "otp":
            # Generate and send OTP
            try:
                otp_code = OTP.create_otp(user)
                
                # Send OTP via SMS (uncomment when ready)
                # send_sms_otp(user)
                
                # For development, store OTP in session
                request.session['otp_user_id'] = user.id
                request.session['otp_code'] = otp_code
                
                # Debug print
                print(f"OTP for {user.contact_number}: {otp_code}")
                
                return redirect(f"/otp/?user_id={user.id}")
            except Exception as e:
                error = f"Failed to send OTP: {str(e)}"

        else:
            error = "Please select a login method"

    return render(request, "accounts/login.html", {"error": error})


def otp_verify_view(request):
    user_id = request.GET.get('user_id') or request.session.get('otp_user_id')
    
    if not user_id:
        return redirect('/login/')
    
    user = get_object_or_404(User, id=user_id)
    
    if request.method == "POST":
        entered_otp = request.POST.get('otp')
        
        if not entered_otp:
            return render(request, "accounts/otp_verify.html", {
                "error": "Please enter OTP",
                "user_id": user_id,
                "mobile": user.contact_number
            })
        
        # Get the latest unused OTP for this user
        try:
            otp_obj = OTP.objects.filter(
                user=user, 
                is_used=False
            ).latest('created_at')
            
            # Check if OTP is valid
            if otp_obj.is_valid() and otp_obj.otp == entered_otp:
                # Mark OTP as used
                otp_obj.is_used = True
                otp_obj.save()
                
                # FIX: Set backend BEFORE login (only once)
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                
                # Log the user in (ONLY ONCE)
                login(request, user)
                
                # Redirect based on role
                if user.role == "admin":
                    return redirect("/admin/")
                elif user.role == "farmer":
                    return redirect("/farmer/dashboard/")
                elif user.role == "buyer":
                    return redirect("/buyer/dashboard/")
                else:
                    return redirect("/dashboard/")
            else:
                error = "Invalid or expired OTP"
        except OTP.DoesNotExist:
            error = "OTP not found or already used"
        
        return render(request, "accounts/otp_verify.html", {
            "error": error,
            "user_id": user_id,
            "mobile": user.contact_number
        })
    
    return render(request, "accounts/otp_verify.html", {
        "user_id": user_id,
        "mobile": user.contact_number
    })
def signup_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        contact_number = request.POST.get("contact_number")
        whatsapp_number = request.POST.get("whatsapp_number")
        email = request.POST.get("email")
        role = request.POST.get("role")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        terms = request.POST.get("terms")
        
        # Validation
        if not all([name, contact_number, role, password, confirm_password, terms]):
            messages.error(request, "All mandatory fields are required")
            return render(request, "accounts/signup.html")
        
        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return render(request, "accounts/signup.html")
        
        # Check if user already exists
        if User.objects.filter(contact_number=contact_number).exists():
            messages.error(request, "User with this mobile number already exists")
            return render(request, "accounts/signup.html")
        
        # Set whatsapp_number to contact_number if empty
        if not whatsapp_number:
            whatsapp_number = contact_number
        
        try:
            # Create user
            user = User.objects.create_user(
                contact_number=contact_number,
                password=password,
                name=name,
                whatsapp_number=whatsapp_number if whatsapp_number else None,
                email=email if email else None,
                role=role
            )
            
            messages.success(request, "Account created successfully! Please login.")
            return redirect("login")
        except Exception as e:
            messages.error(request, f"Error creating account: {str(e)}")
            return render(request, "accounts/signup.html")
    
    return render(request, "accounts/signup.html")


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully")
    return redirect("login")


def resend_otp(request):
    if request.method == "POST":
        user_id = request.POST.get('user_id')
        user = get_object_or_404(User, id=user_id)
        
        try:
            otp_code = OTP.create_otp(user)
            
            # Send OTP via SMS (uncomment when ready)
            # send_sms_otp(user)
            
            request.session['otp_code'] = otp_code
            print(f"Resent OTP for {user.contact_number}: {otp_code}")
            
            return JsonResponse({
                "success": True,
                "message": "OTP resent successfully"
            })
        except Exception as e:
            return JsonResponse({
                "success": False,
                "message": f"Failed to resend OTP: {str(e)}"
            })
    
    return JsonResponse({"success": False, "message": "Invalid request"})
def get_user_backend(user):
    """Determine which backend to use for a user"""
    from django.conf import settings
    
    # Try custom backend first
    try:
        from .backends import ContactNumberBackend
        if ContactNumberBackend().user_can_authenticate(user):
            return 'accounts.backends.ContactNumberBackend'
    except:
        pass
    
    # Fallback to default backends
    for backend in settings.AUTHENTICATION_BACKENDS:
        if 'ModelBackend' in backend:
            return backend
    
    # Default fallback
    return 'django.contrib.auth.backends.ModelBackend'
