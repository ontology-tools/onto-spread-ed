const esbuild = require("esbuild")
const vuePlugin = require("esbuild-plugin-vue3")

const opts = {
    entryPoints: ["js/settings/main.ts"],
    bundle: true,
    outfile: "onto_spread_ed/static/js/settings.js",
    plugins: [vuePlugin({cssInline: true})],
}

if(process.argv.includes("--watch")) {
    esbuild.context(opts).then(x => x.watch())
} else {
    esbuild.build(opts)
}


