#!/usr/bin/env python
"""
Script to verify notification signal handlers are properly set up
"""
import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TakeCare.settings')
django.setup()

def check_signal_handlers():
    """Check which notification signal handlers are enabled"""
    print("Checking notification signal handlers...")
    
    try:
        # Import the signals module
        from notifications import signals
        import inspect
        
        # Check enabled modules
        print("\nModule Integration Status:")
        print(f"- Referrals: {'Enabled' if hasattr(signals, 'REFERRALS_ENABLED') and signals.REFERRALS_ENABLED else 'Disabled'}")
        print(f"- Prescriptions: {'Enabled' if hasattr(signals, 'PRESCRIPTIONS_ENABLED') and signals.PRESCRIPTIONS_ENABLED else 'Disabled'}")
        print(f"- Appointments: {'Enabled' if hasattr(signals, 'APPOINTMENTS_ENABLED') and signals.APPOINTMENTS_ENABLED else 'Disabled'}")
        
        # Check for our new modules
        medical_records_enabled = hasattr(signals, 'MEDICAL_RECORDS_ENABLED') and signals.MEDICAL_RECORDS_ENABLED
        issues_enabled = hasattr(signals, 'ISSUES_ENABLED') and signals.ISSUES_ENABLED
        chat_enabled = hasattr(signals, 'CHAT_ENABLED') and signals.CHAT_ENABLED
        
        print(f"- Medical Records: {'Enabled' if medical_records_enabled else 'Disabled'}")
        print(f"- Issues: {'Enabled' if issues_enabled else 'Disabled'}")
        print(f"- Chat Messages: {'Enabled' if chat_enabled else 'Disabled'}")
        
        # Check signal handlers
        print("\nSignal Handlers:")
        handlers = [name for name, func in inspect.getmembers(signals) 
                   if inspect.isfunction(func) and name.startswith('send_')]
        
        for handler in handlers:
            print(f"- {handler}")
        
        # Check ready function
        if hasattr(signals, 'ready'):
            print("\nReady function is properly defined")
        else:
            print("\nWARNING: No ready function found in signals module")
    
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_signal_handlers()
