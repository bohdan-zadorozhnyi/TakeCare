#!/bin/bash

# This script runs inside the Docker container to test notifications

echo "=== Testing Prescription and Referral Notifications ==="
echo "Running test script inside Docker container..."

# Navigate to the app directory (should be the current directory in most containers)
cd /app

# Run the test script
python test_prescription_referral_notifications.py

# Check the result
if [ $? -eq 0 ]; then
  echo "✅ Tests passed! Notifications are working correctly."
else
  echo "❌ Tests failed. Check the logs for more details."
  echo ""
  echo "Debug suggestions:"
  echo "1. Check if signals are properly registered in apps.py"
  echo "2. Verify model field names match what's being accessed in signal handlers"
  echo "3. Ensure database connection is working properly"
  echo "4. Check the Django logs for more detailed error messages"
fi

# Print environment information for debugging
echo ""
echo "=== Environment Information ==="
echo "Django version: $(python -c 'import django; print(django.get_version())')"
echo "Python version: $(python --version)"
echo "App directory: $(pwd)"
echo "Settings module: $DJANGO_SETTINGS_MODULE"
