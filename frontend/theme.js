import {extendTheme} from "@chakra-ui/react";
import {mode} from "@chakra-ui/theme-tools";

const theme = extendTheme({
    config: {
        initialColorMode: "system",
        useSystemColorMode: false
    },
    fonts: {
        "fit-system": `-apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", 
        "Pretendard Variable", Pretendard, Roboto, "Noto Sans KR", "Segoe UI", 
        "Malgun Gothic", "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", 
        sans-serif`,
        "keep-font": `"Pretendard Variable", Pretendard, -apple-system, 
        BlinkMacSystemFont, system-ui, Roboto, "Helvetica Neue", "Segoe UI", 
        "Apple SD Gothic Neo", "Noto Sans KR", "Malgun Gothic", "Apple Color Emoji", 
        "Segoe UI Emoji", "Segoe UI Symbol", sans-serif`
    },
    space: {
        navheight: "7vh"
    },
    sizes: {
        navheight: "7vh"
    },
    semanticTokens: {
        colors: {
            navbg: {
                default: "white",
                _light: "white",
                _dark: "#222",
            },
            mainbg: {
                default: "white",
                _light: "white",
                _dark: "#151515",
            },
            secondbg: {
                default: "white",
                _light: "white",
                _dark: "#222",
            },
            mainfont: {
                default: "black",
                _light: "black",
                _dark: "white"
            },
            "scrollbar-track": {
                default: "#ffce92",
                _light: "#ffce92",
                _dark: "#c0a1f1"
            },
            "scrollbar-thumb": {
                default: "#ff8f1b",
                _light: "#ff8f1b",
                _dark: "#a16cf1"
            },
            "scrollbar-thumb-hover": {
                default: "#ff6f1b",
                _light: "#ff6f1b",
                _dark: "#7f3cf1"
            },
            bordercolor: {
                default: "gray.200",
                _light: "gray.200",
                _dark: "#333"
            },
            btnbg: {
                default: "white",
                _light: "white",
                _dark: "#222"
            },
            itembg: {
                default: "gray.200",
                _light: "gray.200",
                _dark: "#333"
            }
        },
        shadows: {
            undernav: {
                default: "0 5px 4px 2px rgba(0, 0, 0, .1)",
                _dark: "none"
            },
        },
    },
    styles: {
        global: (props) => ({
            "html,body": {
                width: "100%",
                fontSize: "20px",
                fontFamily: "keep-font",
                bgColor: "mainbg",
                color: "mainfont"
            },
            "div#__next": {
                paddingTop: "navheight",
            }
        }),
    },
})

export default theme