import random
import pygame
import cv2

COLOR_THEME1 = ((10,0,34),(30,30,30),(190,0,0),(20,0,68),(0,0,0),(0,0,60),(0,0,255))
COLOR_THEME2 = ((15,15,15),(60,60,60),(40,40,40),(25,25,25),(0,0,0),(30,30,30),(255,255,255))
COLOR_THEME3 = ((0,0,255),(255,0,0),(0,255,0),(255,255,0),(0,0,0),(255,0,255),(0,255,255))
COLOR_THEME4 = ((0,50,0),(0,0,0),(0,150,0),(0,0,0),(0,255,0),(0,0,0),(0,255,0))

EMPTY, FILLED, PAINTED, SIGNED, BORDER, BACKGROUND, TEXT = COLOR_THEME4

SIZE = (800,600)
CHART_SIZE = (480,600)
BOX_SIZE = (40,40)

game_over = False
score = 0

class Shape:
    O = ((True,True),
        (True,True))
    Z = ((True,True,False),
        (False,True,True))
    Z1 = ((False,True,True),
        (True,True,False))
    L = ((True,False,False),
        (True,True,True))
    L1 = ((False,False,True),
        (True,True,True))
    T = ((False,True,False),
        (True,True,True))
    I = ((True,True,True,True),)
    SHAPES = (O,Z,Z1,L,L1,T,I)
    def __init__(self,x,y):
        self.shape = list(random.choice(self.SHAPES))
        self.prev_shape = None
        self.posx = x
        self.posy = y
        self.lastposx = self.lastposy = None

    def turn(self):
        self.prev_shape = self.shape.copy()
        self.shape =  [[self.shape[j][i] for j in range(len(self.shape) - 1, -1,-1)]\
             for i in range(len(self.shape[0]))] 
    
    def go_back(self):
        self.shape = self.prev_shape.copy()
        self.prev_shape = None

    def set_pos(self,x=None,y=None):
        if x is not None:
            self.lastposx = self.posx
            self.posx = x
        if y is not None:
            self.lastposy = self.posy
            self.posy = y

    def get_pos(self):
        return self.posx, self.posy

    def copy(self):
        s = Shape(self.posx,self.posy)
        s.shape = self.shape.copy()
        return s

class Box(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h) -> None:
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill(BORDER)
        self.image.fill(EMPTY,pygame.Rect(1,1,w-2,h-2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.width = w
        self.height = h
        self.filled = False
        self.painted = False
        self.signed = False

    def update(self):
        if self.painted:
            self.painted = False
            return
        if self.signed:
            self.signed = False
            return
        color = FILLED if self.filled else EMPTY
        self.image.fill(color,pygame.Rect(1,1,self.width-2,self.height-2))

    def paint(self):
        self.image.fill(PAINTED,pygame.Rect(1,1,self.width-2,self.height-2))
        self.painted = True
    
    def sign(self):
        self.image.fill(SIGNED,pygame.Rect(1,1,self.width-2,self.height-2))
        self.signed = True

class ChartBase(pygame.sprite.Sprite):
    def __init__(self,x,y,width,height,box_w,box_h,center=False):
        self.width = width
        self.height = height
        self.box_w = box_w
        self.box_h = box_h
        self.chart = [[Box(x,y,box_w,box_h) for x in range(0, self.width, box_w)] \
            for y in range(0, self.height, box_h)]
        self.shape = None
        self.keys = []
        self.counter = 0
        self.image = pygame.Surface((self.width,self.height))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        if center:
            self.rect.center = (x,y)

    def draw(self,ekran:pygame.Surface):
        self.image.fill(EMPTY)
        for line in self.chart:
            for i in line:
                self.image.blit(i.image,i.rect)
        ekran.blit(self.image,self.rect)
    
    def draw_shape(self):
        for x,line in enumerate(self.shape.shape):
            for y,f in enumerate(line):
                if f:self.chart[self.shape.posx + x][self.shape.posy + y].paint()

    def update_chart(self):
        for line in self.chart:
            for i in line:
                i.update()

class NextShapePreview(ChartBase):
    def __init__(self, x, y, width, height, box_w, box_h, shape, center=False):
        super().__init__(x, y, width, height, box_w, box_h, center)
        self.shape = shape

class Chart(ChartBase):
    def __init__(self, x, y, width, height, box_w, box_h, center=False):
        super().__init__(x, y, width, height, box_w, box_h, center)
        self.next_shape = Shape(0,5)

    def update(self):
        if not self.shape:
            if not self.create_shape(): self.game_over()
        self.move_shape()
        self.draw_shape_shadow()
        self.draw_shape()
        self.scroll_shape()
        self.check_lines()
        self.update_chart()
        self.keys.clear()

    def create_shape(self):
        self.shape = self.next_shape
        self.next_shape = Shape(0,5)
        return self.check_shape(self.shape,self.shape.posx,self.shape.posy)
    
    def check_shape(self,shape,psx,psy):
        for x, line in enumerate(shape.shape):
            for y, i in enumerate(line):
                if not i:
                    continue
                if not 0 <= y + psy <= self.width//self.box_w - 1 or \
                    not 0 <= x + psx <= self.height//self.box_h - 1:
                    return False 
                if self.chart[x + psx][y + psy].filled:
                     return False
        return True

    def move_shape(self):
        x,y = self.shape.get_pos()
        if pygame.key.get_pressed()[pygame.K_DOWN]: x += 1
        if pygame.K_LEFT in self.keys: y -= 1
        if pygame.K_RIGHT in self.keys: y += 1
        if pygame.K_RETURN in self.keys: self.turn_shape()
        self.shape.set_pos(x,y)
        if not self.check_shape(self.shape,*self.shape.get_pos()):
            self.shape.set_pos(self.shape.lastposx,self.shape.lastposy)

    def turn_shape(self):
        self.shape.turn()
        if not self.check_shape(self.shape,*self.shape.get_pos()):
            self.shape.go_back()
    
    def place_shape(self):
        psx,psy = self.shape.get_pos()
        for x, line in enumerate(self.shape.shape):
            for y, i in enumerate(line):
                if not i:
                    continue
                self.chart[x + psx][y + psy].filled = i
        self.shape = None

    def scroll_shape(self):
        self.counter += 1
        if self.counter == 20:
            self.counter = 0
            self.shape.set_pos(self.shape.posx + 1,self.shape.posy)
            if not self.check_shape(self.shape,*self.shape.get_pos()):
                self.shape.set_pos(self.shape.lastposx,self.shape.lastposy)
                self.place_shape()

    def check_lines(self):
        global score
        chart = [[i.filled for i in line] for line in self.chart]
        chart.reverse()
        rmvd_lines = 0
        for i,line in enumerate(chart):
            if all(line):
                chart.pop(i - rmvd_lines)
                chart.append([False for _ in range(len(chart[0]))])
                rmvd_lines += 1
        for x,line in enumerate(reversed(chart)):
            for y,i in enumerate(line):
                self.chart[x][y].filled = i
        score += rmvd_lines

    def draw_next_shape(self,ekran):
        nchart = NextShapePreview(self.width + (SIZE[0] - self.width)/2, SIZE[1]/2,
            len(self.next_shape.shape[0])*BOX_SIZE[0],len(self.next_shape.shape)*BOX_SIZE[1],
            *BOX_SIZE,self.next_shape.copy(),True)
        nchart.shape.posy = nchart.shape.posx = 0
        nchart.draw_shape()
        nchart.draw(ekran)
    
    def draw_shape_shadow(self):
        s = self.shape.copy()
        while self.check_shape(s,*s.get_pos()):
            s.set_pos(s.posx + 1,s.posy)
        s.set_pos(s.lastposx,s.lastposy)
        for x,line in enumerate(s.shape):
            for y,f in enumerate(line):
                if f:self.chart[s.posx + x][s.posy + y].sign()

    def game_over(self):
        global game_over
        game_over = True

def blur(image:pygame.Surface):
    w = image.get_width()
    h = image.get_height()
    kernel = (100,100)
    imgdata = pygame.surfarray.array3d(image)
    blured = cv2.blur(imgdata,kernel)
    image = pygame.surfarray.make_surface(blured)
    return image

def create_chart():
    return Chart(0,0,*CHART_SIZE,*BOX_SIZE)

def main():
    global game_over, score
    ekran = pygame.display.set_mode(SIZE)
    clock = pygame.time.Clock()
    chart = create_chart()
    pygame.font.init()
    f = pygame.font.SysFont("monospace",30,True)
    blurred_background = None
    while True:
        clock.tick(60)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                quit()
            if ev.type == pygame.KEYDOWN:
                chart.keys.append(ev.key)
        if game_over:
            if blurred_background == None:
                blurred_background = blur(ekran)
            ekran.blit(blurred_background,(0,0))
            p = f.render("GAME OVER",True,TEXT)
            p2 = f.render(f"Score : {score}",True,TEXT)
            ekran.blit(p,((SIZE[0]-p.get_width())//2,(SIZE[1]-50-p.get_height())//2))
            ekran.blit(p2,((SIZE[0]-p2.get_width())//2,(SIZE[1]+50-p2.get_height())//2))
            if pygame.K_RETURN in chart.keys:
                chart = create_chart()
                game_over = False
                score = 0
                blurred_background == None
        else:
            ekran.fill(BACKGROUND)
            p = f.render(f" Score : {score}",True,TEXT)
            ekran.blit(p,(CHART_SIZE[0],0))
            chart.update()
            chart.draw(ekran)
            chart.draw_next_shape(ekran)
        pygame.display.update()

if __name__ == "__main__":
    main()