import reflex as rx

config = rx.Config(
    app_name="mindweaver_fe",
    react_strict_mode=False,
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
)
