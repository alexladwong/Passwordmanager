import flet as ft

# -------- Compatibility shims (handles Colors/colors and Icons/icons) --------
COLORS = getattr(ft, "colors", None) or getattr(ft, "Colors")
ICONS = getattr(ft, "icons", None) or getattr(ft, "Icons")

def color_with_opacity(color, opacity: float):
    fn = getattr(COLORS, "with_opacity", None)
    if not fn:
        return color
    try:
        return fn(opacity, color)   # newer signature
    except TypeError:
        try:
            return fn(color, opacity)  # older signature
        except TypeError:
            return color
# -----------------------------------------------------------------------------

# Stores references to progress bars (CONTROLS) and checkboxes (STATUS)
CONTROLS: list[ft.Row] = []
STATUS: list[ft.Row] = []

def store_control(function):
    """Decorator to collect certain UI controls for later updates."""
    def wrapper(*args, **kwargs):
        reference = function(*args, **kwargs)
        if kwargs.get("control", 0) == 0:
            CONTROLS.append(reference)
        else:
            STATUS.append(reference)
        return reference
    return wrapper


class PasswordStrengthChecker:
    def __init__(self, password: str):
        self.password = password or ""

    def length_check(self) -> int:
        n = len(self.password)
        if 0 < n < 8:
            return 0
        elif 8 <= n < 12:
            return 1
        elif 12 <= n < 16:
            return 2
        elif n >= 16:
            return 3
        return 0

    def character_check(self) -> int:
        chars = set(self.password)
        lower = set("abcdefghijklmnopqrstuvwxyz")
        upper = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        digits = set("0123456789")
        special = set(r"~`!@#$%^&*()-_þʼ«æ…+={}[]|/\:;`><.?")  # raw string avoids \: warning

        score = 0
        if any(c in lower for c in chars):
            score += 1
        if any(c in upper for c in chars):
            score += 1
        if any(c in digits for c in chars):
            score += 1
        if any(c in special for c in chars):
            score += 1
        return {1: 0, 2: 1, 3: 2, 4: 3}.get(score, 0)

    def repeat_check(self) -> int:
        p = self.password
        if not p:
            return 2
        for i in range(len(p) - 2):
            if p[i] == p[i + 1] == p[i + 2]:
                return 0
        return 1

    def sequential_check(self) -> int:
        p = self.password
        if not p:
            return 2
        for i in range(len(p) - 2):
            chunk = p[i: i + 3]
            if chunk.isdigit() or chunk.islower() or chunk.isupper():
                return 0
        return 1


class AppWindow(ft.Card):
    def __init__(self):
        super().__init__(elevation=20)
        # state
        self.show_password = False
        self.password_field: ft.TextField | None = None
        self.page: ft.Page | None = None  # set in main()
        # build UI
        self.content = ft.Container(
            width=400,
            height=None,  # let it grow to fit the list + input
            border_radius=10,
            bgcolor="#1f262f",
            content=ft.Column(
                spacing=12,  # space between checklist and input
                horizontal_alignment="center",
                controls=[
                    self.password_strength_display(),
                    ft.Divider(height=4, color="transparent"),
                    self.password_input_display(),
                ],
            ),
        )

    # --- Password logic handlers -------------------------------------------
    def check_password(self, e: ft.ControlEvent):
        checker = PasswordStrengthChecker(e.data or "")
        self.password_length_status(checker.length_check())
        self.character_check_status(checker.character_check())
        self.repeat_check_status(checker.repeat_check())
        self.sequential_check_status(checker.sequential_check())

    def toggle_view(self, e: ft.ControlEvent):
        """Toggle show/hide password and update icon + field."""
        self.show_password = not self.show_password
        if not self.password_field or not self.page:
            return
        self.password_field.password = not self.show_password
        # also flip the eye icon
        e.control.icon = ICONS.VISIBILITY if self.show_password else ICONS.VISIBILITY_OFF
        e.control.update()
        self.page.update()

    def copy_password(self, e: ft.ControlEvent):
        if not self.password_field or not self.page:
            return
        text = self.password_field.value or ""
        # clipboard: try both modern and older names
        set_clip = getattr(self.page, "set_clipboard", None)
        copy_fn = getattr(self.page, "copy_to_clipboard", None)
        try:
            if callable(set_clip):
                set_clip(text)
            elif callable(copy_fn):
                copy_fn(text)
        except Exception:
            pass
        # show snackbar to confirm copy (reuse the page's snackbar)
        sb = getattr(self.page, "snack_bar", None)
        if sb and hasattr(sb, "content"):
            # update existing snackbar content
            if isinstance(sb.content, ft.Text):
                sb.content.value = "Password copied to clipboard"
            else:
                sb.content = ft.Text("Password copied to clipboard")
            sb.bgcolor = getattr(COLORS, "GREEN_400", None) or getattr(COLORS, "GREEN", None)
            sb.open = True
            self.page.update()
        else:
            # fallback: just assign a new one with required content
            self.page.snack_bar = ft.SnackBar(ft.Text("Password copied to clipboard"), open=True)
            self.page.update()

    # --- UI update helpers -------------------------------------------------
    def criteria_satisfied(self, index: int, status: int):
        # Show/hide checkbox tick with opacity only
        if index >= len(STATUS):
            return
        box = STATUS[index].controls[0]
        if status == 3:
            box.opacity = 1
            box.content.value = True
        else:
            box.content.value = False
            box.opacity = 0
        box.update()

    def password_length_status(self, strength: int):
        if not CONTROLS:
            return
        bar = CONTROLS[0].controls[1].controls[0]
        if strength == 0:
            bar.bgcolor, bar.width = COLORS.RED, 40
        elif strength == 1:
            bar.bgcolor, bar.width = COLORS.YELLOW, 70
        elif strength == 2:
            bar.bgcolor, bar.width = COLORS.GREEN_400, 100
        elif strength == 3:
            bar.bgcolor, bar.width = COLORS.GREEN_900, 130
        else:
            bar.width = 0
        bar.opacity = 1
        bar.update()
        self.criteria_satisfied(0, strength)

    def character_check_status(self, strength: int):
        if len(CONTROLS) < 2:
            return
        bar = CONTROLS[1].controls[1].controls[0]
        if strength == 0:
            bar.bgcolor, bar.width = COLORS.RED, 40
        elif strength == 1:
            bar.bgcolor, bar.width = COLORS.YELLOW, 70
        elif strength == 2:
            bar.bgcolor, bar.width = COLORS.GREEN_400, 100
        elif strength == 3:
            bar.bgcolor, bar.width = COLORS.GREEN_900, 130
        else:
            bar.width = 0
        bar.opacity = 1
        bar.update()
        self.criteria_satisfied(1, strength)

    def repeat_check_status(self, strength: int):
        if len(CONTROLS) < 3:
            return
        bar = CONTROLS[2].controls[1].controls[0]
        if strength == 0:
            bar.bgcolor, bar.width = COLORS.RED, 65
        elif strength == 1:
            bar.bgcolor, bar.width = COLORS.GREEN_900, 130
        else:
            bar.width = 0
        bar.opacity = 1
        bar.update()
        self.criteria_satisfied(2, 3 if strength == 1 else strength)

    def sequential_check_status(self, strength: int):
        if len(CONTROLS) < 4:
            return
        bar = CONTROLS[3].controls[1].controls[0]
        if strength == 0:
            bar.bgcolor, bar.width = COLORS.RED, 65
        elif strength == 1:
            bar.bgcolor, bar.width = COLORS.GREEN_900, 130
        else:
            bar.width = 0
        bar.opacity = 1
        bar.update()
        self.criteria_satisfied(3, 3 if strength == 1 else strength)

    # ------------------------- UI building blocks -----------------------------
    @store_control
    def check_criteria_display(self, criteria: str, description: str, control: int):
        return ft.Row(
            alignment="spaceBetween",
            vertical_alignment="center",
            spacing=5,
            controls=[
                ft.Column(
                    spacing=2,
                    controls=[
                        ft.Text(value=criteria, size=12, weight=ft.FontWeight.BOLD, color=COLORS.WHITE),
                        ft.Text(
                            value=description,
                            size=12,
                            color=color_with_opacity(COLORS.WHITE, 0.54),
                        ),
                    ],
                ),
                ft.Row(
                    spacing=0,
                    alignment="start",
                    controls=[
                        ft.Container(
                            height=5,
                            width=0,
                            bgcolor=COLORS.TRANSPARENT,
                            opacity=0,
                            border_radius=10,
                        )
                    ],
                ),
            ],
        )

    @store_control
    def check_status_display(self, control: int):
        return ft.Row(
            alignment="end",
            controls=[
                ft.Container(
                    opacity=0,             # start hidden
                    border_radius=50,
                    width=21,
                    height=21,
                    alignment=ft.alignment.center,
                    content=ft.Checkbox(
                        scale=0.7,
                        fill_color="#7df6dd",
                        check_color=COLORS.BLUE,
                        disabled=True,
                    ),
                ),
            ],
        )

    def password_strength_display(self):
        return ft.Container(
            width=400,
            height=None,  # natural height so input isn't pushed out
            bgcolor="#1f262f",
            border_radius=10,
            padding=10,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=ft.Column(
                horizontal_alignment="center",
                spacing=10,
                controls=[
                    ft.Divider(height=5, color="transparent"),
                    ft.Text("Password Strength Checker", size=24, color=COLORS.WHITE, weight=ft.FontWeight.BOLD),
                    ft.Text("Please input your password and check the strength!", size=14, color=COLORS.WHITE),
                    ft.Divider(height=25, color="transparent"),

                    self.check_criteria_display("1. Length Check", "Strong passwords are 12+ characters", control=0),
                    self.check_status_display(control=1),

                    ft.Divider(height=10, color="transparent"),

                    self.check_criteria_display(
                        "2. Character Check", "Checks upper, lower, digits, and specials", control=0
                    ),
                    self.check_status_display(control=1),

                    ft.Divider(height=10, color="transparent"),

                    self.check_criteria_display("3. Repeat Checker", "Detects triple repeated characters", control=0),
                    self.check_status_display(control=1),

                    ft.Divider(height=10, color="transparent"),

                    self.check_criteria_display(
                        "4. Sequential Checker", "Detects simple sequences (abc/ABC/123)", control=0
                    ),
                    self.check_status_display(control=1),
                ],
            ),
        )

    def password_text_field_display(self):
        # create the TextField once and reuse so handlers can access it
        if self.password_field:
            return ft.Row(
                spacing=20,
                vertical_alignment="center",
                controls=[
                    ft.Icon(name=ICONS.LOCK_OUTLINE_ROUNDED, size=16, opacity=0.85),
                    self.password_field,
                ],
            )

        self.password_field = ft.TextField(
            border_color="transparent",
            bgcolor="transparent",
            height=28,
            width=200,
            text_size=14,
            content_padding=6,
            cursor_color=COLORS.WHITE,
            cursor_width=1,
            color=COLORS.WHITE,
            hint_text="Type password here...",
            on_change=self.check_password,
            password=True,
        )
        return ft.Row(
            spacing=20,
            vertical_alignment="center",
            controls=[
                ft.Icon(name=ICONS.LOCK_OUTLINE_ROUNDED, size=16, opacity=0.85),
                self.password_field,
            ],
        )

    def password_input_display(self):
        # Right side: eye toggle + copy button
        view_icon_name = ICONS.VISIBILITY if self.show_password else ICONS.VISIBILITY_OFF
        return ft.Card(
            width=350,
            height=60,
            elevation=14,
            margin=10,
            content=ft.Container(
                padding=ft.padding.only(left=15, right=10),
                content=ft.Row(
                    alignment="spaceBetween",
                    controls=[
                        self.password_text_field_display(),
                        ft.Row(
                            spacing=6,
                            controls=[
                                ft.IconButton(icon=view_icon_name, icon_size=20, on_click=self.toggle_view),
                                ft.IconButton(icon=ICONS.COPY, icon_size=18, on_click=self.copy_password),
                            ],
                        ),
                    ],
                ),
            ),
        )


def main(page: ft.Page):
    # Reusable snackbar (older Flet needs content arg)
    page.snack_bar = ft.SnackBar(ft.Text(""), open=False)
    app = AppWindow()
    app.page = page  # let the AppWindow use page methods (clipboard / snackbars)
    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"
    page.add(app)
    page.update()


if __name__ == "__main__":
    # On macOS, run with: python main.py
    ft.app(target=main)
