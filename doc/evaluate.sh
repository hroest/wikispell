
cat tests/data/wrong_words.txt | sort > /tmp/wrong
grep '*99' $1 | cut -f 2 -d ' ' | sort > /tmp/found
found=`cat /tmp/found | wc -l`
allp=`cat /tmp/wrong | wc -l`
fn=`comm -32 /tmp/wrong /tmp/found | wc -l `
fp=`comm -31 /tmp/wrong /tmp/found | wc -l `
tp=`echo "$allp - $fn" | bc`
echo "Positives:" $allp
echo "False negatives:" $fn
echo "False positives:" $fp
echo "True positives:" $tp

pr=`echo "$tp / $found * 100" | bc -l`
recall=`echo "$tp / $allp * 100" | bc -l`
fval=`echo "2*$pr * $recall / ($pr + $recall )" | bc -l`
echo "Precision :" $pr
echo "Recall :" $recall
echo "F :" $fval

