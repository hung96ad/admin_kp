sudo apt-get update
sudo apt install unzip -y
sudo apt-get install tesseract-ocr tesseract-ocr-vie -y
sudo su
# root
apt-get install wkhtmltopdf xvfb -y
printf '#!/bin/bash\nxvfb-run -a --server-args="-screen 0, 1024x768x24" /usr/bin/wkhtmltopdf -q $*' > /usr/bin/wkhtmltopdf.sh
chmod a+x /usr/bin/wkhtmltopdf.sh
ln -s /usr/bin/wkhtmltopdf.sh /usr/local/bin/wkhtmltopdf
# user
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
cat .ssh/id_rsa.pub # copy to git
git clone git@github.com:hung96ad/admin_kp.git
sudo apt install python3-pip
pip3 install -r requirements.txt 
cd admin_kp
git checkout hung 
pip3 install -r requirements.txt 
#ngrok
# wget https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip
# unzip ngrok-stable-linux-amd64.zip 
# ./ngrok authtoken 1Vgg71VO8gKgqErchdDmDA1nPE8_7ZuopzfkzbvpdxPEBtqe
# nohup ./ngrok http 5000 &
