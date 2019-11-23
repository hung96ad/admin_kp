import imgkit
import html5lib
import lxml
import os
import shutil
import random
import pdfkit 

def DataFrame_to_image(css, outputfile="out.jpg", format="jpg"):
    fn = str(random.random()*100000000).split(".")[0] + ".html"
    
    try:
        os.remove(fn)
    except:
        None
    text_file = open(fn, "a")
    
    # write the CSS
    text_file.write(css)
    text_file.close()
    
    # See IMGKit options for full configuration,
    # e.g. cropping of final image
    imgkitoptions = {"format": format, "xvfb": ""}
    
    imgkit.from_file(fn, outputfile.replace('pdf', 'jpg'), options=imgkitoptions)
    pdfkit.from_file(fn, outputfile) 
    os.remove(fn)

def gen_by_ho_ten(ho_ten, id_election, line, prefix=''):
    rand = ho_ten.shape[0]
    s = ''
    if rand <= 20:
        step = 1
        for i in range(0, rand, step):
            s += f'<tr><td>{i+1}</td><td>{ho_ten[i]}</td> </tr>'
        html = '''
            <!DOCTYPE html>
            <html>
            <head>
            <meta charset="utf-8"/>
            <style>
            img{
                width:100%;
                max-width:159px;
                height: 100%;
                max-height:159px;
            }
            table, th, td {
              border: 2px solid black;
              border-collapse: collapse;
            }
            th, td {
              padding: 5px;
              text-align: center;
            }
            </style>
            </head>
            <body>
            <div style="width:21cm; height:5cm; position:relative; z-index:1">
                  </div>
            <div style="width:21cm; height:24.7cm; position:relative; z-index:2;">
            <div style="position:relative; left:4.5cm;">
            <h3 style="text-align: center; width:80%;">
            ''' + line[0] +'''<br>
            ''' + line[1] +'''<br>
            ''' + line[2] +'''<br>
            ''' + line[3] +'''<br>
            <br>
            </div>
            <div style="position:relative; left:4.5cm;">
            <table style="width:80%;">
              <tr>
                <th style="width:10px;">TT</th>
                <th>HỌ VÀ TÊN</th>
                </tr>
              '''+ s + '''
            </table>
            </div>
            </div>
            </body>
            </html>
            '''
    else: 
        step = 2
        for i in range(0, rand, step):
            if i+1 >= rand:
                s += f'<tr> <td>{i+1}</td><td>{ho_ten[i]}</td> <td></td><td></td> </tr>'            
            else:
                s += f'<tr> <td>{i+1}</td><td>{ho_ten[i]}</td> <td>{i+2}</td><td>{ho_ten[i+1]}</td> </tr>'
        html = '''
            <!DOCTYPE html>
            <html>
            <head>
            <meta charset="utf-8"/>
            <style>
            img{
                width:100%;
                max-width:159px;
                height: 100%;
                max-height:159px;
            }
            table, th, td {
              border: 2px solid black;
              border-collapse: collapse;
            }
            th, td {
              padding: 5px;
              text-align: center;
            }
            </style>
            </head>
            <body>
            <div style="width:21cm; height:5cm; position:relative; z-index:1">
                  </div>
            <div style="width:21cm; height:24.7cm; position:relative; z-index:2;">
            <div style="position:relative; left:4.5cm;">
            <h3 style="text-align: center; width:80%;">
            ''' + line[0] +'''<br>
            ''' + line[1] +'''<br>
            ''' + line[2] +'''<br>
            ''' + line[3] +'''<br>
            <br>
            </h2>
            </div>
            <div style="position:relative; left:4.5cm;">
            <table style="width:80%;">
              <tr>
                <th style="width:10px;">TT</th>
                <th>HỌ VÀ TÊN</th>
                <th style="width:10px;">TT</th>
                <th>HỌ VÀ TÊN</th>
                </tr>
              '''+s+'''
            </table>
            </div>
            </div>
            </body>
            </html>
            '''
    directory = prefix + "%s/"%id_election
    try:
        shutil.rmtree(directory, ignore_errors=True)
    except:
        print('')
    if not os.path.exists(directory):
        os.makedirs(directory)
    outputfile = directory + "%s.pdf"%id_election
    DataFrame_to_image(html, outputfile=outputfile)
    return outputfile.replace('app', '')