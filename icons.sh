curl -L https://github.com/idesis-gmbh/png2icons/releases/download/v2.0.1/png2icons-linux.zip -o png2icons-linux.zip
unzip png2icons-linux.zip
chmod +x png2icons
./png2icons resources/icon-1024x1024.png icon -allp -bc -i
mv icon.icns resources/ && mv icon.ico resources/
