
from ImageDataset import ImageDataset
from torch.utils.data import DataLoader
from models.unet import UNet
from config.config import training_config
import torch 
from ddpm import DDPMPipeline
from tqdm import tqdm
from pathlib import Path
from utils import postprocess, create_images_grid


def evalulate(config, epoch, pipeline, model):

    # Perform reverse diffusion process with noisy images.
    noisy_sample = torch.randn(
        config.eval_batch_size,
        config.image_channels,
        config.image_size,
        config.image_size
    ).to(config.device)

    # Reverse diffusion for T timesteps
    images = pipeline.sampling(model, noisy_sample, device=config.device)

    # Postprocess and save sampled images 
    images = postprocess(images)
    image_grid = create_images_grid(images=images,
                                    rows=2,
                                    cols=3)
    

    grid_save_dir = Path(config.output_dir, 'samples')
    grid_save_dir.mkdir(parents=True, exist_ok=True)
    image_grid.save(f"{grid_save_dir}/{epoch:04d}.png")


def main():

    train_dataloader = ImageDataset(image_folder="E:\\YouTube\\DDPM-coding\\dataset\\cat_dog_images")
    train_dataloader = DataLoader(dataset=train_dataloader, 
                                  batch_size=6,
                                  shuffle=True)
    

    model = UNet(image_size=training_config.image_size,
                 input_channels=training_config.image_channels).to(training_config.device)
    
    print("Model size: ", sum([p.numel() for p in model.parameters() if p.requires_grad]))

    optimizer = torch.optim.Adam(params=model.parameters(), 
                                 lr=training_config.learning_rate)
    
    lr_scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer=optimizer,
                                                              T_max=len(train_dataloader) * training_config.num_epochs,
                                                              last_epoch=-1,
                                                              eta_min=1e-9)
    


    for param_group in optimizer.param_groups:
        param_group['lr'] = training_config.learning_rate

    diffusion_pipeline = DDPMPipeline(beta_start=1e-4,
                                      beta_end=1e-2,
                                      num_timesteps=training_config.diffusion_timesteps
                                      )
    
    global_step = training_config.start_epoch * len(train_dataloader)

    # Training Loop 
    for epoch in range(training_config.start_epoch, training_config.num_epochs):
        progress_bar = tqdm(total=len(train_dataloader))
        progress_bar.set_description(f"Epoch {epoch}")

        mean_loss = 0 

        model.train()

        for step, batch in enumerate(train_dataloader):

            for batch in train_dataloader:
                original_images = batch.to(training_config.device)

            batch_size = original_images.shape[0]

            # sample a random timestep for epoch image 
            timesteps = torch.randint(low=0,
                                      high=diffusion_pipeline.num_timesteps,
                                      size=(batch_size,),
                                      device=training_config.device).long()
            

            # Apply forward diffusion process at the given timestep 
            noisy_images, noise = diffusion_pipeline.forward_diffusion(original_images, timesteps)
            noisy_images = noisy_images.to(training_config.device)


            # Predict the noise residual 
            noise_pred = model(noisy_images, timesteps)
            loss = torch.nn.functional.mse_loss(input=noise_pred,
                                                target=noise)
            
            # calculate new mean on the run without accumulating all the values 
            mean_loss = mean_loss = (loss.detach().item() - mean_loss) / (step + 1)
            loss.backward()

            torch.nn.utils.clip_grad_norm_(parameters=model.parameters(),
                                           max_norm=1.0)
            optimizer.step()
            lr_scheduler.step()
            optimizer.zero_grad()

            progress_bar.update(1)
            logs = {"loss": mean_loss, 
                    "lr": lr_scheduler.get_last_lr()[0],
                    "step": global_step}
            global_step += 1 


        ## Evaluation 
        if (epoch + 1) % training_config.save_image_epochs == 0 or epoch == training_config.num_epochs - 1:
            model.eval()
            evalulate(config=training_config, 
                      epoch=epoch,
                      pipeline=diffusion_pipeline,
                      model=model)
            

            



        if (epoch + 1) % training_config.save_image_epochs == 0 or epoch == training_config.num_epochs - 1:
            checkpoint = {
                'model': model.state_dict(),
                'optimizer': optimizer.state_dict(),
                'lr_scheduler': lr_scheduler.state_dict(),
                'parameters': training_config,
                'epoch': epoch
            }

            torch.save(checkpoint, Path("checkpoint",
                                        f"unet{training_config.image_size}_e{epoch}.pth"))



if __name__ == "__main__":
    main()