const esbuild = require("esbuild")
const vuePlugin = require("esbuild-plugin-vue3")
const path = require("path")
const fs = require("fs")

const unpluginVue = require('unplugin-vue-components/esbuild')
const bootstrapVueNext = require('bootstrap-vue-next')
const BootstrapVueNextResolver = bootstrapVueNext.BootstrapVueNextResolver 


const Components = unpluginVue.default


const ROOT_DIR = "js"

async function main() {

    const dirs = fs.readdirSync(ROOT_DIR)

    for (const dir of dirs) {
        let entryPoint = path.join("js", dir, "main.ts");
        if (fs.existsSync(entryPoint)) {
            const opts = {
                entryPoints: [entryPoint],
                bundle: true,
                outfile: path.join("onto_spread_ed", "static", "js", `${dir}.js`),
                plugins: [
                    vuePlugin({cssInline: true}),
                    Components({
                        resolvers: [BootstrapVueNextResolver()],
                    })
                ],
                sourcemap: true,
            }

            console.log(`Building ${dir}...`)

            await esbuild.build(opts)
        }
    }

}

main()




