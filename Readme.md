# DDPM paper Implmentation in this Repo
YouTube video: https://www.youtube.com/watch?v=2zCcucNqWIQ&t=9153s

![DDPM Image](Image/denoising-diffusion.png)





### File List Structure (Good for simple structures)

```text
DDPM/
│
├── config/
│   ├── config.py                 # configuration of training model file 
│   
├── models/
│   └── layers.py
|   └── unet.py
│       
└── dataset/
|   └── cat_dog_images/             # cat dog image are found in this file 
|
├── README.md
├── ImageDataset.py
├── train.py
├── utils.py
├── ddpm.py


