/opt/vc/bin/vcgencmd measure_temp
for id in core; do  echo -e "$(vcgencmd measure_volts)" ; done
