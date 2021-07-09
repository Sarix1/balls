import sdl2.ext
#from math import sqrt
from time import sleep

# SDL related initializations
sdl2.ext.init()
width           = 640
height          = 480
window          = sdl2.ext.Window("Balls!", size=(width, height))
window_surface  = window.get_surface()
window_pixels   = sdl2.ext.PixelView(window_surface)
window.show()

# controller class
# technically unnecessary, but having keyboard input code directly manipulate physics is really goddamn messy, so should always be separated
# like using this as a "middle-man", thus making it possible also to manipulate controls by A.I, demo playback, etc. without extra code
class Controller:
    left  = 0
    right = 0
    up    = 0
    down  = 0

class Ball:
    # default location is 0 0
    x = 0
    y = 0
    # default velocity is 0 0
    vel_x = 0
    vel_y = 0
    # default colour values give a red ball, unless redefined at initialization
    r = 255
    g = 0
    b = 0
    # the controller object stores information if we are steering left, right, up, down
    controller = Controller()
    
    def __init__(self, size, x, y, sprite_surface):
        # physics
        self.x            = x
        self.y            = y
        self.size         = size
        self.radius       = size / 2.0
        self.bounce_x     = bounce          # assigned from global default value; x axis bounce-back
        self.bounce_y     = bounce          # assigned from global default value; y axis bounce-back
        self.accelerate   = accelerate      # assigned from global default value; rate of increasing x velocity by controlling
        self.max_move_vel = max_move_vel    # assigned from global default value; maximum velocity to apply when controlling
        self.jump_vel     = jump_vel        # assigned from global default value; negative y velocity applied for jumping
        self.floating     = 0               # determines whether the object is floating in air or standing on the bottom edge of the screen border

        # graphics
        # use the sprite which we got as an argument
        self.sprite_surface = sprite_surface
        # if we got None as argument, generate a new, red ball sphere
        if self.sprite_surface == None:
            self.sprite_surface = make_ball_sprite(self.size, 255, 0, 0, 0.66)
    
    # read input from controller object and apply incremental changes to velocity
    def do_control(self):
        # if the input for left == 1 and vel is not yet -max_move_vel ("greater than" negative max_move_vel),
        # accelerate with a negative value (toward left on x axis)
        if self.controller.left and self.vel_x > -self.max_move_vel:
            self.vel_x -= self.accelerate
        # if the input for right == 1 and vel is less than max_move_vel, increase x vel by 1
        if self.controller.right and self.vel_x < self.max_move_vel:
            self.vel_x += self.accelerate
        # if we pressed up and the ball is NOT floating (therefore it's on the ground), "jump" by setting y vel to -20
        if self.controller.up and not self.floating:
            self.vel_y = -self.jump_vel
    
    # apply physics-caused changes to velocity, then manipulate x y position based on x y velocity
    def do_physics(self):
        # apply gravity to y vel, incrementally making the object fall faster downwards
        if self.floating:
            self.vel_y += gravity

        # horizontal friction when touching floor, scale the vel down
        if not self.floating:
            self.vel_x *= friction
        # when x velocity drops below a set threshold (stop_vel), stop it entirely to prevent a slow eternal slide
        if abs(self.vel_x) < stop_vel:
            self.vel_x = 0
        
        # apply current velocities to position values
        self.x += self.vel_x
        self.y += self.vel_y

    # test for collision against screen borders, and perform necessary actions  
    def do_edge_collision(self):
        ################# x collision #################
        # left edge
        if self.x - self.radius < 0:
            # if we crossed over the left screen edge, move the ball right exactly by
            # the difference between the ball's leftmost point and the left screen edge, so its edge touches the border
            self.x -= self.x - self.radius
            # reverse velocity for a "bounce" effect
            if self.vel_x < 0:
                self.do_bounce_x()

        # same shit for right edge
        elif self.x + self.radius > width-1:
            # if we crossed over the right screen edge, move the ball back enough so it's inside, its edge touching the border, again
            self.x -= self.x + self.radius - width
            # reverse velocity for a "bounce" effect
            if self.vel_x > 0:
                self.do_bounce_x()

        ################# y collision ####################
        # top edge
        if self.y - self.radius < 0:
            self.y -= self.y - self.radius
            if self.vel_y < 0:
                self.do_bounce_y()

        # bottom edge
        elif self.y + self.radius > height-1:
            self.y -= self.y + self.radius - height
            if self.vel_y > 0:
                self.do_bounce_y()
            # since we're touching the floor, we are NOT floating in air; set floating to 0
            self.floating = 0
        else:
            # otherwise we clearly are floating in the air, high as a kite
            self.floating = 1

    # the below functions could also cause some bouncy squeezy animation to play  
    def do_bounce_x(self):
        self.vel_x *= self.bounce_x
        
    def do_bounce_y(self):   
        self.vel_y *= self.bounce_y
        
    # draw function, to copy the ball's (pre-calculated, pre-drawn) image surface, or "sprite", onto the window surface
    def draw(self):
        # the blitsurface function copies sprite_surface to window_surface
        # it's much faster than setting pixels one by one via PixelView
        # the "None" could be replaced with: sdl.SDL_Rect(x, y, w, h) if we only wanted to copy part of the sprite
        # such as if it's actually a sprite sheet graphic, and we're just copying one piece, representing one frame
        # the SDL_Rect that __is__ there, is the destination coordinates (x, y, w, h) on the screen where we want to draw
        # you could scale the sprite larger or smaller along x and y axes by inserting different values for w and h there
        # instead of BlitSurface, we use BlitScaled; exact same, except Scaled will resize the source surface to the given area
        sdl2.SDL_BlitScaled(
            self.sprite_surface,        # source surface
            None,                       # source rectangle
            window_surface,             # target surface
            sdl2.SDL_Rect(              # target rectangle           
                int(self.x - self.size//2), # target rect. start x
                int(self.y - self.size//2), # target rect. start y
                self.size,                  # target rect. width
                self.size                   # target rect. height
            )
        )
        # the function is written on multiple lines for the sake of clarity, but could be written on one line all the same;
        # such as the original blitsurface version of the function, commented out below
        # sdl2.SDL_BlitSurface(self.sprite_surface, None, window_surface, sdl2.SDL_Rect(int(self.x-self.radius), int(self.y-self.radius), self.size, self.size))
        

def draw_circle(x, y, radius, r, g, b, target_pixels, shaded):
    # cast coordinates into integers, since they might be fractional numbers,
    # but we need integers to know which exact pixels to reference
    x = int(x)
    y = int(y)

    # turn a flag on to create an extra pixel if the circle radius would produce even numbered coordinates
    # (e.g. if the circle is 100 x 100, it must have 4 pixels in the middle)
    # % 1 gets the fractional part of any number (e.g. 10.75 gives 0.75), abs() gets the absolute value (e.g. -0.1 becomes 0.1)
    # k must be 1 for even numbered, and 0 for odd numbered coordinates
    if abs((radius % 1) - 0.5) < 0.5:
        k = 0
    else:
        k = 1

    # now that we don't need the fractional part anymore, we cast the radius to an integer, rounding down
    # if k is 0, we inferred from the radius that the circle size is closer to an odd number
    # in this case the rounding down "loses" an odd pixel along each dimension, and so we add 1 to the radius
    radius = int(radius) + (1-k)

    # we need these 2ndary variables if the circle is shaded; explained below
    new_r = r
    new_g = g
    new_b = b

    # squared radius for an optimization trick; explained below
    radius_squared = radius**2
    
    # process each pixel in a squrae area; not the whole pixel area of the ball, just one quadrant of it
    for y_pix in range (0, radius):
        for x_pix in range (0, radius):
            # get each pixel's distance from the square's centre
            # distance = math.sqrt(y_pix**2 + x_pix**2)
            # instead of getting the square root of the distance every time,
            # we get the square of the radius once at the beginning of the function (above)
            # and compare the squared values; the mathematical outcome in comparing which is greater, is the exact same! :O
            # but now we have saved ourselves lots of processing power, and don't need the sqrt library!
            distance_squared = y_pix**2 + x_pix**2
            # if the pixel is within a radius, draw it; otherwise leave it empty
            if distance_squared < radius_squared:
                # if the circle is shaded, modify r,g,b values using distance/radius ratio and shaded modifier
                if shaded != 0:
                    # shaded == 1 gives a fully shaded ball, almost black near edges
                    # (think like: 1 * 100% of red is reduced from red if distance/radius == 1.0)
                    # (think like: 1 * 50% of red is reduced from red if distance/radius == 0.5)

                    # shaded == 0.5 gives a half-shaded ball, which has half-brightness of original colour near the edges
                    # (think like: 0.5 * 100% == 50% of red is reduced from red if distance/radius == 1.0)
                    # (think like: 0.5 * 50% == 25% of red is reduced from red if distance/radius == 0.5)
                    
                    # shaded == 0 is not shaded at all, plain colour

                    # please note that we have to calculate a new shaded colour for each pixel,
                    # while preserving the original r, g, b values; hence we need the new_r, new_g, new_b variables
                    new_r = r - int(shaded * r * (distance_squared / radius_squared))
                    new_g = g - int(shaded * g * (distance_squared / radius_squared))
                    new_b = b - int(shaded * b * (distance_squared / radius_squared))

                # we do 4 pixels at a time, just flipping - and + for coordinate offsets from x and y
                # we do the math above for one quadrant of the image, but write a mirrored pixel into all four quadrants
                # since the circle image is symmetrical on x and y axes, this saves time and processing power
                # you could even calculate just 1 octant and draw 8 pixels in all octants, but that would overcomplicate the code for this example

                try:
                    target_pixels[y - y_pix - k][x - x_pix - k] = sdl2.ext.Color(new_r, new_g, new_b)
                    target_pixels[y - y_pix - k][x + x_pix]     = sdl2.ext.Color(new_r, new_g, new_b)
                    target_pixels[y + y_pix]    [x - x_pix - k] = sdl2.ext.Color(new_r, new_g, new_b)
                    target_pixels[y + y_pix]    [x + x_pix]     = sdl2.ext.Color(new_r, new_g, new_b)
                except:
                    print("Warning: attempting to draw outside of boundaries!")

def make_ball_sprite(size, r, g, b, shaded):
    # a surface is just data containing pixel graphics, like an image
    # because SDL_CreateRGBSurface() returns a memory address (pointer) to a surface, instead of a surface itself...
    p_sprite_surface = sdl2.SDL_CreateRGBSurface(0, size, size, 32, 0xff000000, 0x00ff0000, 0x0000ff00, 0x000000ff)
    # ...we need to create another variable from the contents (actual surface) at that memory address
    sprite_surface = p_sprite_surface.contents
    # in order to be able to manipulate the pixels of the image, we need this PixelView thing to "unlock" its memory
    sprite_pixels = sdl2.ext.PixelView(sprite_surface)
    # with all that shit done, we can finally fucking draw some shit on the image
    # start coordinates are size // 2, since the x, y given to draw_circle are its middle point
    draw_circle(size//2, size//2, size/2, r, g, b, sprite_pixels, 0.75)

    # now that we're finished manipulating the surface's pixels, return the surface to whoever called
    return sprite_surface

def process_events(control):
    # get_events() gets a "queue" list of all kinds of happenings from keyboard, mouse, whatever
    # these things are called events, though in other contexts the word can also refer to in-game events (player died, grenade exploded...)
    events = sdl2.ext.get_events()

    # you can then walk through this queue of events using a for loop, and check for the ones you want
    # see https://wiki.libsdl.org/SDL_EventType for a complete list
    for event in events:
        # function returns False to the while (running) loop, making running = False
        # and thus exit the loop - and also exit the program
        if event.type == sdl2.SDL_QUIT:
            return False
    
    # SDL_GetKeyboardState(None) creates a data structure that contains status of all keyboard buttons
    # please keep in mind that get_events() must be called first or else there is nothing
    keyboard_state  = sdl2.SDL_GetKeyboardState(None)

    # the control object given as argument to this function is used to store 1 or 0 for left, right, up, down
    # depending on if that key element on the keyboard_state list is 1 or 0
    # for a full list, see list of SDL_SCANCODE_ * in https://wiki.libsdl.org/SDL_Scancode
    control.left    = keyboard_state[sdl2.SDL_SCANCODE_LEFT]
    control.right   = keyboard_state[sdl2.SDL_SCANCODE_RIGHT]
    control.up      = keyboard_state[sdl2.SDL_SCANCODE_UP]
    control.down    = keyboard_state[sdl2.SDL_SCANCODE_DOWN]

    # don't forget to return True to the main loop that calls this function, so running = True
    return True

# global physics variables
gravity       = 1             # rate at which vel_y increases every cycle to simulate gravity
friction      = 0.8           # multiplier for scaling x velocity when colliding with bottom edge
bounce        = -0.9          # multiplier for reversing velocity when an object collides and bounces off
stop_vel      = 0.25          # threshold below which velocity is set to 0
accelerate    = 1             # rate at which vel_x changes when controlling left/right
max_move_vel  = 8             # stop applying left/right force once max vel reached
jump_vel      = 20            # y_vel to be applied for jumping (as a negative value -> up)
# a quick physics lesson:
# https://i.imgur.com/9qKajZI.png
# * speed is how fast you are travelling, e.g. car travelling at speed of 20 m/s
# * velocity is speed in a given direction, e.g. a car is travelling east at a velocity of 10/ms
# velocity is usually a vector, i.e. information represented using two or three axises, so:
# a car with a north velocity (y axis) of 10 m/s and east velocity (x axis) of 10 m/s would have an actual speed of ~14.1 m/s
# that is why we use the word velocity, and seldom call anything speed





################## MAIN PROGRAM EXECUTION ##########################

# globals for testing
color = sdl2.ext.Color(255, 0, 255)
# let's create some balls because why not
# 1st ball should auto-generate its own red ball sprite because we give None as the sprite surface argument
Ball1 = Ball(100, 200, 200, None)    
Ball1.vel_x = 0
Ball1.vel_y = 0
Ball1.bounce_y = 0 # disable the vertical bouncing to make this ball easier to control

# let's make a blue sprite for the 2nd ball
# we purposefully make the sprite smaller than teh ball, to see that BlitScaled will scale the sprite up
# to the target drawing area on the screen
blue_ball_sprite = make_ball_sprite(15, 100, 100, 255, 0.66)

# and the 2nd ball that uses it
Ball2 = Ball(50, 100, 200, blue_ball_sprite)  
Ball2.vel_x = -50
Ball2.vel_y = -10

# Let's make a 3rd ball that uses the same sprite image too
Ball3 = Ball(100, 400, 200, blue_ball_sprite)    
Ball3.vel_x = 0
Ball3.vel_y = 0

# just to prove a point, let's edit the blue ball sprite by adding a green square to it
# and see that the change shows up in both blue balls, proving they don't store unique copies
# but instead, have memory pointers to the same graphic!
sdl2.ext.fill(blue_ball_sprite, sdl2.ext.Color(0, 255, 0), (5, 5, 5, 5))
# just for the sake of completeness and rehearsal, let's also see how to add just 1 pixel, a red dot at the centre
blue_ball_sprite_pixels = sdl2.ext.PixelView(blue_ball_sprite)
blue_ball_sprite_pixels[7][7] = sdl2.ext.Color(255, 0, 0)

# could be called main(), run(), execute() or whatever
def run():
    # example of a game loop, demonstrating in which order to execute things
    running = True
    while running == True:
        ######################## 1. GET INPUT & PROCESS EVENTS ####################################
        # get player input into Ball1.controller and check events for quitting,
        # set running to False if quit, otherwise True
        running = process_events(Ball1.controller)


        ######################## 2. LOGIC PROCESSING (physics, AI, etc.) ########################
        # now that we processed events and stored keyboard state into Ball1.controller,
        # first alter the Ball1's velocity using its control() function
        Ball1.do_control()
        # then work out physics, first gravity, then how friction affects vel values,
        # and then move the ball's physical location (x, y) based on the final vel values
        Ball1.do_physics()
        Ball2.do_physics()
        Ball3.do_physics()
        # since the ball has been moved now, we must check if it has collided, and do things like
        # correct its position if it went through the edge, or change velocity values to "bounce" it off
        Ball1.do_edge_collision()
        Ball2.do_edge_collision()
        Ball3.do_edge_collision()
        # for countless more balls, it would make more sense for program code to look like this:
        # list_of_balls = []
        # list_of_balls.append(Ball(size_here, some_x, some_y, some_sprite or None))
        # ...
        # for ball in list_of_balls:
        #   ball.do_some_thing()
        # ...
        # for ball in list_of_balls:
        #   ball.do_another_thing()
        # ...
        # you would certainly need to do this for things like particles, bullets, etc. which there are 100s or 1000s
        # because you cannot write individual variables and class instances for each of them
        

        ############ 3. GRAPHICS UPDATE (draw the screen and all objects on top of it) ############
        # clear screen with black background
        sdl2.ext.fill(window_surface, color, (0, 0, width, height))
        # with the balls now in their final positions after all the calculations done above,
        # draw the balls over the black background
        Ball1.draw()     
        Ball2.draw()
        Ball3.draw()
        # refresh the window
        window.refresh()
        sleep(1/60) # <- this ...
        # doesn't actually mean we get 60 FPS, just that we get a 1/60 second delay,
        # no matter how long the game frame took to process

# program start
run()
