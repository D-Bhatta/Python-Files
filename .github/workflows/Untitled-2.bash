python_version=$(python3.10 --version)
echo $python_version
start_check_formatting_create_environment=$(TZ=UTC date --rfc-3339=ns)
stop_check_formatting_create_environment=$(TZ=UTC date --rfc-3339=ns)
start_check_formatting_run_black=$(TZ=UTC date --rfc-3339=ns)
stop_check_formatting_run_black=$(TZ=UTC date --rfc-3339=ns)
echo "# Check code formatting with black"
echo ""
echo "\`\`\`json"
echo "{"
echo "\"name\": \"Check code formatting with black\","
echo "\"time_now\": \"$(TZ=UTC date --rfc-3339=ns)\","
echo "\"venv-cache.outputs.cache-hit\": \"$STEPS_VENV_CACHE_OUTPUTS_CACHE_HIT\""
echo "\"start_check_formatting_create_environment\": \"$start_check_formatting_create_environment\","
echo "\"stop_check_formatting_create_environment\": \"$stop_check_formatting_create_environment\","
echo "\"check_formatting_env_info\": \"$check_formatting_env_info\","
echo "\"start_check_formatting_run_black\": \"$start_check_formatting_run_black\","
echo "\"stop_check_formatting_run_black\": \"$stop_check_formatting_run_black\""
echo "}"
echo "\`\`\`"
echo ""
