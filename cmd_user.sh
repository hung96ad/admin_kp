sudo apt-get update
sudo apt install unzip -y
sudo apt-get install tesseract-ocr tesseract-ocr-vie -y
sudo locale-gen vi_VN
sudo update-locale LANG=vi_VN
export LC_ALL="vi_VN.UTF-8"
sudo su
apt-get install wkhtmltopdf xvfb -y
printf '#!/bin/bash\nxvfb-run -a --server-args="-screen 0, 1024x768x24" /usr/bin/wkhtmltopdf -q $*' > /usr/bin/wkhtmltopdf.sh
chmod a+x /usr/bin/wkhtmltopdf.sh
ln -s /usr/bin/wkhtmltopdf.sh /usr/local/bin/wkhtmltopdf
exit
# user
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
cat .ssh/id_rsa.pub # copy to git
git clone git@github.com:hung96ad/admin_kp.git
cd admin_kp
sudo apt install python3-pip
git checkout server
pip3 install -r requirements.txt 
# run 
nohup python3 run &