
# Check that SIM is defined, exit otherwise
if [[ -z $SIM ]]
then
    echo "SIM is not defined, exiting"
    exit 1
fi

RET_VAL=`grep -l failure results_${SIM}.log`
echo "RET_VAL is |$RET_VAL|"
if [[ -n $RET_VAL ]]
then
    echo "Test failures found for SIM=${SIM}:"
    exit 1
fi

echo "All testcases passed for SIM=${SIM}:"
grep testcase results_${SIM}.log | sort

exit 0
