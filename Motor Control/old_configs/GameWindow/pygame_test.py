
import pygame 
import sys
 
pygame.init() 
  
res_x = 400
res_y = 320

win = pygame.display.set_mode((res_x, res_y)) 
  

pygame.display.set_caption("Snipe-E") 
  
# object current co-ordinates  
x = 200
y = 200
  
# dimensions of the object  
radius = 20

# velocity / speed of movement 
vel = 2

# Indicates pygame is running 
run = True
font = pygame.font.Font('freesansbold.ttf', 16) 


#Safe Operation region
xlim = 200
ylim = 200

#stopping consitions
x_stop = res_x/2-(xlim/2)
y_stop = res_y/2-(ylim/2)

# infinite loop  
while run: 
    # creates time delay of 10ms  
    pygame.time.delay(10) 
         
    for event in pygame.event.get(): 
          
        if event.type == pygame.QUIT: 
            run = False

    keys = pygame.key.get_pressed() 
      
    if keys[pygame.K_ESCAPE]:        
        pygame.quit()
        sys.exit()
    if keys[pygame.K_a] and x>x_stop+radius:        
        x -= vel 
    if keys[pygame.K_d] and x<x_stop+xlim-radius: 
        x += vel    
    if keys[pygame.K_w] and y>y_stop+radius: 
        y -= vel    
    if keys[pygame.K_s] and y<y_stop+ylim-radius: 
        y += vel 
          
    win.fill((0, 0, 0)) 
      
    pygame.draw.circle(win, (255, 0, 0), (x, y),radius) 

    text = font.render(str(x)+","+str(y), True, (0,0,255))
   
    pygame.draw.rect(win,(0,255,0),(res_x/2-(xlim/2),res_y/2-(ylim/2),xlim,ylim),1)

    # for the coordinates display
    textRect = text.get_rect()
    textRect.center = (res_x - 50, res_y-25)
    win.blit(text,textRect)
    
    pygame.display.update()  
  
  
pygame.quit() 


