const esbuild = require("esbuild")
const vuePlugin = require("esbuild-plugin-vue3")

const opts = {
    entryPoints: ["js/release/main.ts"],
    bundle: true,
    outfile: "onto_spread_ed/static/js/release.js",
    plugins: [vuePlugin({cssInline: true})],
}

if(process.argv.includes("--watch")) {
    esbuild.context(opts).then(x => x.watch())
} else {
    esbuild.build(opts)
}


