from aqt import mw


class Sparkle:
    def __init__(self) -> None:
        self.run_js()

    def run_js(self) -> None:
        js = """
            (() => {
            if (!document.getElementById("sparkle-style")) {
                const sparkleStyle = document.createElement("style")
                sparkleStyle.id = "sparkle-style"
                document.head.appendChild(sparkleStyle)
                sparkleStyle.sheet.insertRule(
                `
                @keyframes sparkle {
                    0% {
                    opacity: 0;
                    }
                    25% {
                    opacity: 1;
                    }
                    100% {
                    opacity: 0;
                    }
                }`,
                0
                )
            }

            let sparkle = document.getElementById("sparkle")
            if (sparkle) {
                sparkle.remove()
            }

            sparkle = document.createElement("div")
            sparkle.id = "sparkle"
            sparkle.innerHTML = "✨"
            style = `
                position: absolute;
                top: 24px;
                left: 24px;
                animation: sparkle 1.2s forwards;
            `
            sparkle.style = style

            card = document.getElementById("qa")
            card.appendChild(sparkle)
            })()
            """

        if not mw:
            return

        mw.web.eval(js)
