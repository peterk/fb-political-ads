echo "Exporting to $1"
mkdir $1
python export_data.py $1
cp -r static/ad $1
zip -rq static/SE_political_ads_2018.zip $1
