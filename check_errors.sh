RET_VAL=`grep xxxfailure results.log`
echo "RET_VAL is |$RET_VAL|"
if [[ -n $RET_VAL ]]
then
    exit 1
fi
exit 0