RET_VAL=`grep -l failure results.log`
echo "RET_VAL is |$RET_VAL|"
if [[ -n $RET_VAL ]]
then
    exit 1
fi

echo "All testcases passed:"
grep testcase results.log | sort

exit 0
