import reflex as rx

config = rx.Config(
    app_name="mindweaver_fe",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)