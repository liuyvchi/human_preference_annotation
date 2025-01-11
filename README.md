# preference annotator

Load two folders and manually annotate the preference for each image pair from the two image folders.


```pip install PyQt5 Pillow```

then run


```python image_preference.py```


## Steps

- load image folder A ([Google drive](https://drive.google.com/drive/folders/10PwFh1z7TYansiyvGyP2ls73vkl1V1Z_?usp=drive_link))
- load image folder B
  ** Please only keep the images you need to annotate in the two folders.**
  ** Please select correct folder when loading image folder.**
- load the prompt json file (imgName2prompt.json)
- (optional) load the previsouly saved annotation json file 
- begin to anotate. Select the image you prefere. (click the buttom ```left```, ```right```, or ```no preference```)
- exit and save your annotations
  ** The system will automatically save your annotations as annotations.json. This file can also be used to resume your annotation**

 <img src="step_1_2.jpg" alt="load two folders" width="300">
 <img src="step_3_4.jpg" alt="load two folders" width="400">
