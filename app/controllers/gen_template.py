import html5lib
import lxml
import os
import shutil
import random
import pdfkit 

def DataFrame_to_image(css, outputfile="out.pdf"):
    fn = str(random.random()*100000000).split(".")[0] + ".html"
    
    try:
        os.remove(fn)
    except:
        None
    text_file = open(fn, "a")
    
    # write the CSS
    text_file.write(css)
    text_file.close()
    
    
    pdfkit.from_file(fn, outputfile) 
    

    os.remove(fn)

def gen_by_ho_ten(ho_ten, id_election, line, prefix=''):
    rand = ho_ten.shape[0]
    s = ''
    footer = '''</div></body></html>'''
    header = '''<!DOCTYPE html>
            <html>
            <head>
            <meta charset="utf-8"/>
            <style>
            table, th, td {
              border: 2px solid black;
              border-collapse: collapse;
            }
            table.center {
              margin-left:auto; 
              margin-right:auto;
            }
            th, td {
              padding: 5px;
              text-align: center;
            }
            </style>
            </head>
            <body>
            <div style="width:26cm; height:7cm; position:relative; z-index:1;">

                  </div>
            <div style="width:26cm; height:30cm; position:relative; z-index:2; font-size: 120%;">
            <div style="position:relative;">

            <div style="text-align: center;font-size: 130%;">
            ''' + line[0].upper() +'''<br>
            ''' + line[1].upper() +'''<br>
            ''' + line[2].upper() +'''<br>
            <br>
            </div>
            </div>'''
    if rand <= 19:
        step = 1
        for i in range(0, rand, step):
            s += f'<tr><td style="width:1.0cm; height:1.0cm;">{i+1}</td><td style="width:11cm; height:1.0cm;">{ho_ten[i]}</td> </tr>'
        table = '''<table class="center">
              <tr>
                <td style="width:1.0cm; height:1.0cm;">TT</td>
                <td style="width:11cm; height:1.0cm;">HỌ VÀ TÊN</td>
                </tr>
              '''+ s + '''
            </table>'''
    else: 
        step = 2
        for i in range(0, rand, step):
            if i+1 >= rand:
                s += f'<tr> <td style="width:1.0cm; height:1.0cm;">{i+1}</td><td style="width:11cm; height:1.0cm;">{ho_ten[i]}</td> <td style="width:1.0cm; height:1.0cm;"></td><td style="width:11cm; height:1.0cm;"></td> </tr>'            
            else:
                s += f'<tr> <td style="width:1.0cm; height:1.0cm;">{i+1}</td><td style="width:11cm; height:1.0cm;">{ho_ten[i]}</td> <td style="width:1.0cm; height:1.0cm;">{i+2}</td><td style="width:11cm; height:1.0cm;">{ho_ten[i+1]}</td> </tr>'
        table = '''<table class="center">
              <tr>
                <td style="width:1.0cm; height:1.0cm;"">TT</td>
                <td style="width:11.0cm; height:1.0cm;">HỌ VÀ TÊN</td>
                <td style="width:1.0cm; height:1.0cm;">TT</td>
                <td style="width:11.0cm; height:1.0cm;">HỌ VÀ TÊN</td>
                </tr>
              '''+s+'''
            </table>'''
    html = header + table + footer
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