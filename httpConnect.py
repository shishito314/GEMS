import urllib.request
import time

baseUrl = "http://10.0.0.242/"
url = baseUrl
flag = "Flag_"

while True:
  page = urllib.request.urlopen(url).read()
  temp = str(page)[8:13]
  # print(temp)
  url = baseUrl + flag + "Temp:" + temp
  time.sleep(1)
