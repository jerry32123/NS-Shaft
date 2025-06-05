import pygame
import random
import sys
import os  # 用于文件检查

# 初始化pygame
pygame.init()

# 尝试初始化混音器（用于音频播放）
try:
    pygame.mixer.init()
    mixer_initialized = True
except pygame.error:
    mixer_initialized = False
    print("警告: 音频系统初始化失败，无法播放音乐和音效")

# 游戏窗口设置
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("NS-Shaft 简化版")

# 确保中文正常显示
pygame.font.init()
font_path = pygame.font.match_font('simsun') or pygame.font.match_font('simhei')
if not font_path:
    # 如果找不到中文字体，使用默认字体
    font = pygame.font.Font(None, 24)
else:
    font = pygame.font.Font(font_path, 24)

# 游戏状态
MENU = 0
GAME = 1
INSTRUCTIONS = 2

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)

# 尝试加载背景图片
use_background_image = False
background_image = None

try:
    background_image = pygame.image.load('background.png').convert()
    background_image = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    use_background_image = True
except (pygame.error, FileNotFoundError) as e:
    print(f"无法加载背景图片: {e}")
    print("将使用黑色背景代替")

# 音乐和音效设置
use_background_music = False
use_sound_effects = False

# 背景音乐
background_music = None
if mixer_initialized and os.path.exists('background_music.mp3'):
    try:
        pygame.mixer.music.load('background_music.mp3')
        pygame.mixer.music.set_volume(0.3)  # 音量设置为30%
        use_background_music = True
    except pygame.error as e:
        print(f"无法加载背景音乐: {e}")

# 音效
jump_sound = None
bounce_sound = None
break_sound = None
game_over_sound = None

if mixer_initialized:
    # 跳跃音效
    if os.path.exists('jump.wav'):
        try:
            jump_sound = pygame.mixer.Sound('jump.wav')
            jump_sound.set_volume(0.5)
            use_sound_effects = True
        except pygame.error as e:
            print(f"无法加载跳跃音效: {e}")

    # 弹跳平台音效
    if os.path.exists('bounce.wav'):
        try:
            bounce_sound = pygame.mixer.Sound('bounce.wav')
            bounce_sound.set_volume(0.6)
            use_sound_effects = True
        except pygame.error as e:
            print(f"无法加载弹跳音效: {e}")

    # 破碎平台音效
    if os.path.exists('break.wav'):
        try:
            break_sound = pygame.mixer.Sound('break.wav')
            break_sound.set_volume(0.4)
            use_sound_effects = True
        except pygame.error as e:
            print(f"无法加载破碎音效: {e}")

    # 游戏结束音效
    if os.path.exists('game_over.wav'):
        try:
            game_over_sound = pygame.mixer.Sound('game_over.wav')
            game_over_sound.set_volume(0.7)
            use_sound_effects = True
        except pygame.error as e:
            print(f"无法加载游戏结束音效: {e}")

# 游戏常量
FPS = 60
PLAYER_SIZE = 20
PLATFORM_WIDTH = 60
PLATFORM_HEIGHT = 10
PLATFORM_SPEED = 1
MAX_PLATFORM_SPEED = 1.5  # 平台速度上限
GRAVITY = 0.5
JUMP_POWER = -12
MAX_FALL_SPEED = 15
MAX_PLATFORMS = 15  # 最大平台数量

# 平台类型
PLATFORM_NORMAL = 0
PLATFORM_MOVING = 1
PLATFORM_BREAKING = 2
PLATFORM_BOUNCY = 3


# 玩家类 (继承自pygame.sprite.Sprite)
class Player(pygame.sprite.Sprite):
    def __init__(self, game):
        super().__init__()
        self.game = game  # 引用游戏实例以访问音效
        self.width = PLAYER_SIZE
        self.height = PLAYER_SIZE
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.color = BLUE
        self.health = 100
        self.level = 0  # 重命名为level，避免与精灵组图层冲突

        # 创建精灵图像和矩形
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(self.color)
        self.rect = self.image.get_rect()
        self.rect.x = SCREEN_WIDTH // 2
        self.rect.y = SCREEN_HEIGHT // 2

    def update(self):
        # 应用重力
        self.vel_y += GRAVITY
        if self.vel_y > MAX_FALL_SPEED:
            self.vel_y = MAX_FALL_SPEED

        # 更新位置
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y

        # 边界检查
        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

        # 检查是否在地面上
        self.on_ground = False

    def jump(self):
        if self.on_ground:
            self.vel_y = JUMP_POWER
            # 播放跳跃音效
            if use_sound_effects and jump_sound:
                jump_sound.play()

    def move_left(self):
        self.vel_x = -5

    def move_right(self):
        self.vel_x = 5

    def stop(self):
        self.vel_x = 0

    def check_collision(self, platforms):
        # 只检测玩家附近的平台（优化碰撞检测）
        nearby_platforms = [p for p in platforms if
                            abs(p.rect.y - self.rect.y) < SCREEN_HEIGHT / 2]

        for platform in nearby_platforms:
            if (self.rect.bottom >= platform.rect.top and
                    self.rect.bottom <= platform.rect.top + 10 and
                    self.rect.right >= platform.rect.left and
                    self.rect.left <= platform.rect.right and
                    self.vel_y > 0):
                self.on_ground = True
                self.vel_y = 0
                self.rect.bottom = platform.rect.top
                return platform

        return None


# 平台类 (继承自pygame.sprite.Sprite)
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, platform_type=PLATFORM_NORMAL, game=None):
        super().__init__()
        self.game = game  # 引用游戏实例以访问音效
        self.width = PLATFORM_WIDTH
        self.height = PLATFORM_HEIGHT
        self.type = platform_type
        self.move_direction = 1  # 1 向右，-1 向左
        self.move_speed = 2
        self.break_timer = 0

        # 创建精灵图像和矩形
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(self.get_color())
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def get_color(self):
        if self.type == PLATFORM_NORMAL:
            return GREEN
        elif self.type == PLATFORM_MOVING:
            return BLUE
        elif self.type == PLATFORM_BREAKING:
            return RED
        elif self.type == PLATFORM_BOUNCY:
            return YELLOW
        return GRAY

    def update(self):
        # 移动平台
        if self.type == PLATFORM_MOVING:
            self.rect.x += self.move_direction * self.move_speed
            if self.rect.left <= 0 or self.rect.right >= SCREEN_WIDTH:
                self.move_direction *= -1

        # 破碎平台
        if self.type == PLATFORM_BREAKING and self.break_timer > 0:
            self.break_timer -= 1
            # 1秒后平台完全消失
            if self.break_timer == 0:
                return True  # 平台消失

        return False

    def on_collision(self):
        if self.type == PLATFORM_BREAKING:
            self.break_timer = FPS  # 设置为FPS值，即1秒后消失
            # 播放破碎音效
            if use_sound_effects and break_sound and self.game:
                break_sound.play()
            # 可选：添加平台闪烁效果
            # self.image.fill((255, 100, 100))  # 碰撞后变为更亮的红色
        elif self.type == PLATFORM_BOUNCY:
            # 播放弹跳音效
            if use_sound_effects and bounce_sound and self.game:
                bounce_sound.play()
            return True  # 弹力平台
        return False


# 游戏类
class Game:
    def __init__(self):
        self.player = Player(self)  # 传递游戏实例到玩家
        self.all_sprites = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        self.platform_speed = PLATFORM_SPEED
        self.score = 0
        self.game_over = False
        self.paused = False
        self.font = font
        self.music_playing = False

        # 添加玩家到精灵组
        self.all_sprites.add(self.player)

        # 预渲染静态UI元素（优化渲染性能）
        self.paused_surface = self._create_paused_surface()
        self.game_over_surface = self._create_game_over_surface()

        self.create_initial_platforms()

    def create_initial_platforms(self):
        # 创建玩家起始平台（确保为弹簧平台）
        start_platform_x = SCREEN_WIDTH // 2 - PLATFORM_WIDTH // 2
        start_platform_y = SCREEN_HEIGHT - 100
        start_platform = Platform(start_platform_x, start_platform_y, PLATFORM_BOUNCY, self)

        self.platforms.add(start_platform)
        self.all_sprites.add(start_platform)

        # 将玩家位置设置为起始平台上方
        self.player.rect.x = start_platform_x + PLATFORM_WIDTH // 2 - PLAYER_SIZE // 2
        self.player.rect.y = start_platform_y - PLAYER_SIZE
        self.player.on_ground = True
        self.player.vel_y = 0

        # 生成其他随机平台
        for i in range(10):
            x = random.randint(0, SCREEN_WIDTH - PLATFORM_WIDTH)
            y = random.randint(SCREEN_HEIGHT // 2, SCREEN_HEIGHT - 150) - i * 60
            # 确保前3个平台为普通平台，降低初始难度
            if i < 3:
                platform_type = PLATFORM_NORMAL
            else:
                platform_type = random.randint(0, 3)

            platform = Platform(x, y, platform_type, self)
            self.platforms.add(platform)
            self.all_sprites.add(platform)

    def update(self):
        if self.game_over or self.paused:
            return

        # 启动背景音乐（如果可用且未播放）
        if use_background_music and not self.music_playing:
            pygame.mixer.music.play(-1)  # -1表示循环播放
            self.music_playing = True

        # 更新玩家
        self.player.update()

        # 检查平台碰撞
        platform = self.player.check_collision(self.platforms)
        if platform:
            if platform.on_collision():
                self.player.vel_y = JUMP_POWER * 1.5  # 弹力平台跳得更高

            # 更新层数
            if platform.rect.y < SCREEN_HEIGHT // 2 and platform.rect.y > self.player.rect.y:
                self.player.level += 1  # 修改为level
                self.score += 10

        # 更新平台并移除需要消失的平台
        for platform in list(self.platforms):
            platform.rect.y += self.platform_speed
            if platform.update():
                self.platforms.remove(platform)
                self.all_sprites.remove(platform)
                continue

            # 移除离开屏幕的平台
            if platform.rect.top > SCREEN_HEIGHT:
                self.platforms.remove(platform)
                self.all_sprites.remove(platform)

        # 生成新平台
        if len(self.platforms) < MAX_PLATFORMS:
            x = random.randint(0, SCREEN_WIDTH - PLATFORM_WIDTH)
            y = random.randint(-50, 0)
            platform_type = random.randint(0, 3)

            platform = Platform(x, y, platform_type, self)
            self.platforms.add(platform)
            self.all_sprites.add(platform)

        # 增加难度（限制平台速度上限）
        if self.score % 100 == 0 and self.score > 0 and self.platform_speed < MAX_PLATFORM_SPEED:
            self.platform_speed += 0.1

        # 检查游戏结束条件
        if self.player.rect.y > SCREEN_HEIGHT or self.player.rect.y < -50 or self.player.health <= 0:
            self.game_over = True
            # 播放游戏结束音效
            if use_sound_effects and game_over_sound:
                game_over_sound.play()
            # 停止背景音乐
            if use_background_music:
                pygame.mixer.music.stop()
                self.music_playing = False

        # 尖刺天花板
        if self.player.rect.y < 0:
            self.player.health -= 10
            self.player.vel_y = 5

    def draw(self, surface):
        if use_background_image:
            surface.blit(background_image, (0, 0))
        else:
            surface.fill(BLACK)

        # 绘制所有精灵（优化渲染）
        self.all_sprites.draw(surface)

        # 绘制UI
        health_text = self.font.render(f"生命值: {self.player.health}", True, WHITE)
        layer_text = self.font.render(f"层数: {self.player.level}", True, WHITE)
        speed_text = self.font.render(f"速度: {self.platform_speed:.1f}", True, WHITE)
        score_text = self.font.render(f"分数: {self.score}", True, WHITE)

        surface.blit(health_text, (10, 10))
        surface.blit(layer_text, (10, 40))
        surface.blit(speed_text, (10, 70))
        surface.blit(score_text, (10, 100))

        # 显示音频状态
        if mixer_initialized:
            sound_status = "音效: 开启" if use_sound_effects else "音效: 关闭"
            sound_text = self.font.render(sound_status, True, WHITE)
            surface.blit(sound_text, (10, 130))

            music_status = "音乐: 开启" if use_background_music else "音乐: 关闭"
            music_text = self.font.render(music_status, True, WHITE)
            surface.blit(music_text, (10, 160))

        # 绘制暂停提示（使用预渲染的surface）
        if self.paused:
            surface.blit(self.paused_surface, (0, 0))

        # 绘制尖刺天花板
        for i in range(SCREEN_WIDTH // 20 + 1):
            pygame.draw.polygon(surface, RED, [(i * 20, 0), (i * 20 + 10, 15), (i * 20 + 20, 0)])

        # 游戏结束画面（使用预渲染的surface）
        if self.game_over:
            surface.blit(self.game_over_surface, (0, 0))
            final_score_text = self.font.render(f"最终分数: {self.score}", True, WHITE)
            surface.blit(final_score_text, (SCREEN_WIDTH // 2 - final_score_text.get_width() // 2, SCREEN_HEIGHT // 2))

    def _create_paused_surface(self):
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 180))

        paused_text = self.font.render("游戏暂停", True, WHITE)
        continue_text = self.font.render("按 P 键继续", True, WHITE)

        surf.blit(paused_text, (SCREEN_WIDTH // 2 - paused_text.get_width() // 2, SCREEN_HEIGHT // 2 - 25))
        surf.blit(continue_text, (SCREEN_WIDTH // 2 - continue_text.get_width() // 2, SCREEN_HEIGHT // 2 + 25))

        return surf

    def _create_game_over_surface(self):
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 180))

        over_text = self.font.render("游戏结束!", True, WHITE)
        restart_text = self.font.render("按 R 键重新开始", True, WHITE)
        exit_text = self.font.render("按 Q 键退出游戏", True, WHITE)

        surf.blit(over_text, (SCREEN_WIDTH // 2 - over_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
        surf.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 50))
        surf.blit(exit_text, (SCREEN_WIDTH // 2 - exit_text.get_width() // 2, SCREEN_HEIGHT // 2 + 80))

        return surf

    def toggle_pause(self):
        self.paused = not self.paused
        # 暂停/恢复背景音乐
        if use_background_music:
            if self.paused:
                pygame.mixer.music.pause()
            else:
                pygame.mixer.music.unpause()

    def restart(self):
        self.__init__()


# 主游戏循环
def main():
    clock = pygame.time.Clock()
    game = Game()
    current_state = MENU

    # 菜单字体
    title_font = pygame.font.Font(font_path, 48) if font_path else pygame.font.Font(None, 48)
    menu_font = pygame.font.Font(font_path, 28) if font_path else pygame.font.Font(None, 28)

    # 预渲染菜单元素（优化性能）
    title_text = title_font.render("NS-Shaft", True, WHITE)
    start_text = menu_font.render("按 ENTER 开始游戏", True, WHITE)
    instructions_text = menu_font.render("按 I 查看游戏说明", True, WHITE)
    exit_text = menu_font.render("按 Q 退出游戏", True, WHITE)

    # 预渲染说明元素
    instructions_title = menu_font.render("游戏说明：P键暂停游戏", True, WHITE)
    instruction1 = menu_font.render("左右方向键控制角色移动", True, WHITE)
    instruction2 = menu_font.render("空格键或上方向键跳跃", True, WHITE)
    instruction3 = menu_font.render("绿：普通平台 蓝：移动平台", True, WHITE)
    instruction4 = menu_font.render("黄：弹簧平台 红：破碎平台", True, WHITE)
    back_text = menu_font.render("按 I 返回菜单", True, WHITE)

    running = True
    while running:
        # 事件处理优化
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if current_state == MENU:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        current_state = GAME
                    elif event.key == pygame.K_i:
                        current_state = INSTRUCTIONS
                    elif event.key == pygame.K_q:
                        running = False

            elif current_state == INSTRUCTIONS:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_i:
                        current_state = MENU

            elif current_state == GAME:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                        game.player.jump()
                    if event.key == pygame.K_r and game.game_over:
                        game.restart()
                    if event.key == pygame.K_q and game.game_over:
                        running = False
                    if event.key == pygame.K_p:
                        game.toggle_pause()
                    if event.key == pygame.K_ESCAPE:
                        current_state = MENU
                        game.restart()
                        # 停止背景音乐
                        if use_background_music:
                            pygame.mixer.music.stop()
                            game.music_playing = False

        # 持续按键检测（仅在游戏状态下）
        if current_state == GAME and not game.paused:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                game.player.move_left()
            elif keys[pygame.K_RIGHT]:
                game.player.move_right()
            else:
                game.player.stop()

        # 更新游戏状态（仅在游戏状态下）
        if current_state == GAME:
            game.update()

        # 渲染
        if use_background_image:
            screen.blit(background_image, (0, 0))
        else:
            screen.fill(BLACK)

        if current_state == MENU:
            # 绘制预渲染的菜单元素
            screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 150))
            screen.blit(start_text, (SCREEN_WIDTH // 2 - start_text.get_width() // 2, 300))
            screen.blit(instructions_text, (SCREEN_WIDTH // 2 - instructions_text.get_width() // 2, 350))
            screen.blit(exit_text, (SCREEN_WIDTH // 2 - exit_text.get_width() // 2, 400))

            # 显示音频状态
            if mixer_initialized:
                sound_status = "音效: 开启" if use_sound_effects else "音效: 关闭"
                sound_text = menu_font.render(sound_status, True, WHITE)
                screen.blit(sound_text, (SCREEN_WIDTH // 2 - sound_text.get_width() // 2, 450))

                music_status = "音乐: 开启" if use_background_music else "音乐: 关闭"
                music_text = menu_font.render(music_status, True, WHITE)
                screen.blit(music_text, (SCREEN_WIDTH // 2 - music_text.get_width() // 2, 480))

        elif current_state == INSTRUCTIONS:
            # 绘制预渲染的说明元素
            screen.blit(instructions_title, (SCREEN_WIDTH // 2 - instructions_title.get_width() // 2, 150))
            screen.blit(instruction1, (SCREEN_WIDTH // 2 - instruction1.get_width() // 2, 200))
            screen.blit(instruction2, (SCREEN_WIDTH // 2 - instruction2.get_width() // 2, 250))
            screen.blit(instruction3, (SCREEN_WIDTH // 2 - instruction3.get_width() // 2, 300))
            screen.blit(instruction4, (SCREEN_WIDTH // 2 - instruction3.get_width() // 2, 350))
            screen.blit(back_text, (SCREEN_WIDTH // 2 - back_text.get_width() // 2, 500))

        elif current_state == GAME:
            game.draw(screen)
            # 显示返回菜单提示
            if not game.game_over:
                hint_text = menu_font.render("按 ESC 返回菜单", True, (200, 200, 200))
                screen.blit(hint_text, (10, SCREEN_HEIGHT - 30))

        # 更新显示
        pygame.display.flip()

        # 控制帧率
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()