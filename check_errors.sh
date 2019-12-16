
RET_VAL=`grep failure results.log`
if [[ -n $RET_VAL ]]
then
    exit 1
fi
exit 0