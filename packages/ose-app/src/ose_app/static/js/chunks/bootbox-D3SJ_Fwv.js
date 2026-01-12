function e(l){return new Promise(o=>{bootbox.prompt({...l,callback(n){o(n??null)}})})}function t(l,o="hide"){return new Promise(n=>{let i=null;bootbox.alert({...l,onHidden(){o==="hidden"&&n(i)},callback(a){o==="hidden"?i=a??null:n(a??null)}})})}function c(l){return new Promise(o=>{bootbox.confirm({...l,callback(n){o(n)}})})}export{t as a,c,e as p};
//# sourceMappingURL=bootbox-D3SJ_Fwv.js.map
