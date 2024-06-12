"""
 Copyright (C) 2024 Michael Piazza

 This file is part of Smart Notes.

 Smart Notes is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 Smart Notes is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with Smart Notes.  If not, see <https://www.gnu.org/licenses/>.
"""

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
