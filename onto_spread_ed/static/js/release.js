"use strict";
(() => {
  // node_modules/@vue/shared/dist/shared.esm-bundler.js
  // @__NO_SIDE_EFFECTS__
  function makeMap(str) {
    const map2 = /* @__PURE__ */ Object.create(null);
    for (const key of str.split(","))
      map2[key] = 1;
    return (val) => val in map2;
  }
  var EMPTY_OBJ = true ? Object.freeze({}) : {};
  var EMPTY_ARR = true ? Object.freeze([]) : [];
  var NOOP = () => {
  };
  var NO = () => false;
  var isOn = (key) => key.charCodeAt(0) === 111 && key.charCodeAt(1) === 110 && // uppercase letter
  (key.charCodeAt(2) > 122 || key.charCodeAt(2) < 97);
  var isModelListener = (key) => key.startsWith("onUpdate:");
  var extend = Object.assign;
  var remove = (arr, el) => {
    const i = arr.indexOf(el);
    if (i > -1) {
      arr.splice(i, 1);
    }
  };
  var hasOwnProperty = Object.prototype.hasOwnProperty;
  var hasOwn = (val, key) => hasOwnProperty.call(val, key);
  var isArray = Array.isArray;
  var isMap = (val) => toTypeString(val) === "[object Map]";
  var isSet = (val) => toTypeString(val) === "[object Set]";
  var isDate = (val) => toTypeString(val) === "[object Date]";
  var isFunction = (val) => typeof val === "function";
  var isString = (val) => typeof val === "string";
  var isSymbol = (val) => typeof val === "symbol";
  var isObject = (val) => val !== null && typeof val === "object";
  var isPromise = (val) => {
    return (isObject(val) || isFunction(val)) && isFunction(val.then) && isFunction(val.catch);
  };
  var objectToString = Object.prototype.toString;
  var toTypeString = (value) => objectToString.call(value);
  var toRawType = (value) => {
    return toTypeString(value).slice(8, -1);
  };
  var isPlainObject = (val) => toTypeString(val) === "[object Object]";
  var isIntegerKey = (key) => isString(key) && key !== "NaN" && key[0] !== "-" && "" + parseInt(key, 10) === key;
  var isReservedProp = /* @__PURE__ */ makeMap(
    // the leading comma is intentional so empty string "" is also included
    ",key,ref,ref_for,ref_key,onVnodeBeforeMount,onVnodeMounted,onVnodeBeforeUpdate,onVnodeUpdated,onVnodeBeforeUnmount,onVnodeUnmounted"
  );
  var isBuiltInDirective = /* @__PURE__ */ makeMap(
    "bind,cloak,else-if,else,for,html,if,model,on,once,pre,show,slot,text,memo"
  );
  var cacheStringFunction = (fn) => {
    const cache = /* @__PURE__ */ Object.create(null);
    return (str) => {
      const hit = cache[str];
      return hit || (cache[str] = fn(str));
    };
  };
  var camelizeRE = /-(\w)/g;
  var camelize = cacheStringFunction(
    (str) => {
      return str.replace(camelizeRE, (_, c) => c ? c.toUpperCase() : "");
    }
  );
  var hyphenateRE = /\B([A-Z])/g;
  var hyphenate = cacheStringFunction(
    (str) => str.replace(hyphenateRE, "-$1").toLowerCase()
  );
  var capitalize = cacheStringFunction((str) => {
    return str.charAt(0).toUpperCase() + str.slice(1);
  });
  var toHandlerKey = cacheStringFunction(
    (str) => {
      const s = str ? `on${capitalize(str)}` : ``;
      return s;
    }
  );
  var hasChanged = (value, oldValue) => !Object.is(value, oldValue);
  var invokeArrayFns = (fns, ...arg) => {
    for (let i = 0; i < fns.length; i++) {
      fns[i](...arg);
    }
  };
  var def = (obj, key, value, writable = false) => {
    Object.defineProperty(obj, key, {
      configurable: true,
      enumerable: false,
      writable,
      value
    });
  };
  var looseToNumber = (val) => {
    const n = parseFloat(val);
    return isNaN(n) ? val : n;
  };
  var _globalThis;
  var getGlobalThis = () => {
    return _globalThis || (_globalThis = typeof globalThis !== "undefined" ? globalThis : typeof self !== "undefined" ? self : typeof window !== "undefined" ? window : typeof global !== "undefined" ? global : {});
  };
  function normalizeStyle(value) {
    if (isArray(value)) {
      const res = {};
      for (let i = 0; i < value.length; i++) {
        const item = value[i];
        const normalized = isString(item) ? parseStringStyle(item) : normalizeStyle(item);
        if (normalized) {
          for (const key in normalized) {
            res[key] = normalized[key];
          }
        }
      }
      return res;
    } else if (isString(value) || isObject(value)) {
      return value;
    }
  }
  var listDelimiterRE = /;(?![^(]*\))/g;
  var propertyDelimiterRE = /:([^]+)/;
  var styleCommentRE = /\/\*[^]*?\*\//g;
  function parseStringStyle(cssText) {
    const ret = {};
    cssText.replace(styleCommentRE, "").split(listDelimiterRE).forEach((item) => {
      if (item) {
        const tmp = item.split(propertyDelimiterRE);
        tmp.length > 1 && (ret[tmp[0].trim()] = tmp[1].trim());
      }
    });
    return ret;
  }
  function normalizeClass(value) {
    let res = "";
    if (isString(value)) {
      res = value;
    } else if (isArray(value)) {
      for (let i = 0; i < value.length; i++) {
        const normalized = normalizeClass(value[i]);
        if (normalized) {
          res += normalized + " ";
        }
      }
    } else if (isObject(value)) {
      for (const name in value) {
        if (value[name]) {
          res += name + " ";
        }
      }
    }
    return res.trim();
  }
  var HTML_TAGS = "html,body,base,head,link,meta,style,title,address,article,aside,footer,header,hgroup,h1,h2,h3,h4,h5,h6,nav,section,div,dd,dl,dt,figcaption,figure,picture,hr,img,li,main,ol,p,pre,ul,a,b,abbr,bdi,bdo,br,cite,code,data,dfn,em,i,kbd,mark,q,rp,rt,ruby,s,samp,small,span,strong,sub,sup,time,u,var,wbr,area,audio,map,track,video,embed,object,param,source,canvas,script,noscript,del,ins,caption,col,colgroup,table,thead,tbody,td,th,tr,button,datalist,fieldset,form,input,label,legend,meter,optgroup,option,output,progress,select,textarea,details,dialog,menu,summary,template,blockquote,iframe,tfoot";
  var SVG_TAGS = "svg,animate,animateMotion,animateTransform,circle,clipPath,color-profile,defs,desc,discard,ellipse,feBlend,feColorMatrix,feComponentTransfer,feComposite,feConvolveMatrix,feDiffuseLighting,feDisplacementMap,feDistantLight,feDropShadow,feFlood,feFuncA,feFuncB,feFuncG,feFuncR,feGaussianBlur,feImage,feMerge,feMergeNode,feMorphology,feOffset,fePointLight,feSpecularLighting,feSpotLight,feTile,feTurbulence,filter,foreignObject,g,hatch,hatchpath,image,line,linearGradient,marker,mask,mesh,meshgradient,meshpatch,meshrow,metadata,mpath,path,pattern,polygon,polyline,radialGradient,rect,set,solidcolor,stop,switch,symbol,text,textPath,title,tspan,unknown,use,view";
  var MATH_TAGS = "annotation,annotation-xml,maction,maligngroup,malignmark,math,menclose,merror,mfenced,mfrac,mfraction,mglyph,mi,mlabeledtr,mlongdiv,mmultiscripts,mn,mo,mover,mpadded,mphantom,mprescripts,mroot,mrow,ms,mscarries,mscarry,msgroup,msline,mspace,msqrt,msrow,mstack,mstyle,msub,msubsup,msup,mtable,mtd,mtext,mtr,munder,munderover,none,semantics";
  var isHTMLTag = /* @__PURE__ */ makeMap(HTML_TAGS);
  var isSVGTag = /* @__PURE__ */ makeMap(SVG_TAGS);
  var isMathMLTag = /* @__PURE__ */ makeMap(MATH_TAGS);
  var specialBooleanAttrs = `itemscope,allowfullscreen,formnovalidate,ismap,nomodule,novalidate,readonly`;
  var isSpecialBooleanAttr = /* @__PURE__ */ makeMap(specialBooleanAttrs);
  var isBooleanAttr = /* @__PURE__ */ makeMap(
    specialBooleanAttrs + `,async,autofocus,autoplay,controls,default,defer,disabled,hidden,inert,loop,open,required,reversed,scoped,seamless,checked,muted,multiple,selected`
  );
  function includeBooleanAttr(value) {
    return !!value || value === "";
  }
  function looseCompareArrays(a, b) {
    if (a.length !== b.length)
      return false;
    let equal = true;
    for (let i = 0; equal && i < a.length; i++) {
      equal = looseEqual(a[i], b[i]);
    }
    return equal;
  }
  function looseEqual(a, b) {
    if (a === b)
      return true;
    let aValidType = isDate(a);
    let bValidType = isDate(b);
    if (aValidType || bValidType) {
      return aValidType && bValidType ? a.getTime() === b.getTime() : false;
    }
    aValidType = isSymbol(a);
    bValidType = isSymbol(b);
    if (aValidType || bValidType) {
      return a === b;
    }
    aValidType = isArray(a);
    bValidType = isArray(b);
    if (aValidType || bValidType) {
      return aValidType && bValidType ? looseCompareArrays(a, b) : false;
    }
    aValidType = isObject(a);
    bValidType = isObject(b);
    if (aValidType || bValidType) {
      if (!aValidType || !bValidType) {
        return false;
      }
      const aKeysCount = Object.keys(a).length;
      const bKeysCount = Object.keys(b).length;
      if (aKeysCount !== bKeysCount) {
        return false;
      }
      for (const key in a) {
        const aHasKey = a.hasOwnProperty(key);
        const bHasKey = b.hasOwnProperty(key);
        if (aHasKey && !bHasKey || !aHasKey && bHasKey || !looseEqual(a[key], b[key])) {
          return false;
        }
      }
    }
    return String(a) === String(b);
  }
  function looseIndexOf(arr, val) {
    return arr.findIndex((item) => looseEqual(item, val));
  }
  var isRef = (val) => {
    return !!(val && val["__v_isRef"] === true);
  };
  var toDisplayString = (val) => {
    return isString(val) ? val : val == null ? "" : isArray(val) || isObject(val) && (val.toString === objectToString || !isFunction(val.toString)) ? isRef(val) ? toDisplayString(val.value) : JSON.stringify(val, replacer, 2) : String(val);
  };
  var replacer = (_key, val) => {
    if (isRef(val)) {
      return replacer(_key, val.value);
    } else if (isMap(val)) {
      return {
        [`Map(${val.size})`]: [...val.entries()].reduce(
          (entries, [key, val2], i) => {
            entries[stringifySymbol(key, i) + " =>"] = val2;
            return entries;
          },
          {}
        )
      };
    } else if (isSet(val)) {
      return {
        [`Set(${val.size})`]: [...val.values()].map((v) => stringifySymbol(v))
      };
    } else if (isSymbol(val)) {
      return stringifySymbol(val);
    } else if (isObject(val) && !isArray(val) && !isPlainObject(val)) {
      return String(val);
    }
    return val;
  };
  var stringifySymbol = (v, i = "") => {
    var _a;
    return (
      // Symbol.description in es2019+ so we need to cast here to pass
      // the lib: es2016 check
      isSymbol(v) ? `Symbol(${(_a = v.description) != null ? _a : i})` : v
    );
  };

  // node_modules/@vue/reactivity/dist/reactivity.esm-bundler.js
  function warn(msg, ...args) {
    console.warn(`[Vue warn] ${msg}`, ...args);
  }
  var activeEffectScope;
  var EffectScope = class {
    constructor(detached = false) {
      this.detached = detached;
      this._active = true;
      this.effects = [];
      this.cleanups = [];
      this._isPaused = false;
      this.parent = activeEffectScope;
      if (!detached && activeEffectScope) {
        this.index = (activeEffectScope.scopes || (activeEffectScope.scopes = [])).push(
          this
        ) - 1;
      }
    }
    get active() {
      return this._active;
    }
    pause() {
      if (this._active) {
        this._isPaused = true;
        let i, l;
        if (this.scopes) {
          for (i = 0, l = this.scopes.length; i < l; i++) {
            this.scopes[i].pause();
          }
        }
        for (i = 0, l = this.effects.length; i < l; i++) {
          this.effects[i].pause();
        }
      }
    }
    /**
     * Resumes the effect scope, including all child scopes and effects.
     */
    resume() {
      if (this._active) {
        if (this._isPaused) {
          this._isPaused = false;
          let i, l;
          if (this.scopes) {
            for (i = 0, l = this.scopes.length; i < l; i++) {
              this.scopes[i].resume();
            }
          }
          for (i = 0, l = this.effects.length; i < l; i++) {
            this.effects[i].resume();
          }
        }
      }
    }
    run(fn) {
      if (this._active) {
        const currentEffectScope = activeEffectScope;
        try {
          activeEffectScope = this;
          return fn();
        } finally {
          activeEffectScope = currentEffectScope;
        }
      } else if (true) {
        warn(`cannot run an inactive effect scope.`);
      }
    }
    /**
     * This should only be called on non-detached scopes
     * @internal
     */
    on() {
      activeEffectScope = this;
    }
    /**
     * This should only be called on non-detached scopes
     * @internal
     */
    off() {
      activeEffectScope = this.parent;
    }
    stop(fromParent) {
      if (this._active) {
        this._active = false;
        let i, l;
        for (i = 0, l = this.effects.length; i < l; i++) {
          this.effects[i].stop();
        }
        this.effects.length = 0;
        for (i = 0, l = this.cleanups.length; i < l; i++) {
          this.cleanups[i]();
        }
        this.cleanups.length = 0;
        if (this.scopes) {
          for (i = 0, l = this.scopes.length; i < l; i++) {
            this.scopes[i].stop(true);
          }
          this.scopes.length = 0;
        }
        if (!this.detached && this.parent && !fromParent) {
          const last = this.parent.scopes.pop();
          if (last && last !== this) {
            this.parent.scopes[this.index] = last;
            last.index = this.index;
          }
        }
        this.parent = void 0;
      }
    }
  };
  function getCurrentScope() {
    return activeEffectScope;
  }
  var activeSub;
  var pausedQueueEffects = /* @__PURE__ */ new WeakSet();
  var ReactiveEffect = class {
    constructor(fn) {
      this.fn = fn;
      this.deps = void 0;
      this.depsTail = void 0;
      this.flags = 1 | 4;
      this.next = void 0;
      this.cleanup = void 0;
      this.scheduler = void 0;
      if (activeEffectScope && activeEffectScope.active) {
        activeEffectScope.effects.push(this);
      }
    }
    pause() {
      this.flags |= 64;
    }
    resume() {
      if (this.flags & 64) {
        this.flags &= ~64;
        if (pausedQueueEffects.has(this)) {
          pausedQueueEffects.delete(this);
          this.trigger();
        }
      }
    }
    /**
     * @internal
     */
    notify() {
      if (this.flags & 2 && !(this.flags & 32)) {
        return;
      }
      if (!(this.flags & 8)) {
        batch(this);
      }
    }
    run() {
      if (!(this.flags & 1)) {
        return this.fn();
      }
      this.flags |= 2;
      cleanupEffect(this);
      prepareDeps(this);
      const prevEffect = activeSub;
      const prevShouldTrack = shouldTrack;
      activeSub = this;
      shouldTrack = true;
      try {
        return this.fn();
      } finally {
        if (activeSub !== this) {
          warn(
            "Active effect was not restored correctly - this is likely a Vue internal bug."
          );
        }
        cleanupDeps(this);
        activeSub = prevEffect;
        shouldTrack = prevShouldTrack;
        this.flags &= ~2;
      }
    }
    stop() {
      if (this.flags & 1) {
        for (let link = this.deps; link; link = link.nextDep) {
          removeSub(link);
        }
        this.deps = this.depsTail = void 0;
        cleanupEffect(this);
        this.onStop && this.onStop();
        this.flags &= ~1;
      }
    }
    trigger() {
      if (this.flags & 64) {
        pausedQueueEffects.add(this);
      } else if (this.scheduler) {
        this.scheduler();
      } else {
        this.runIfDirty();
      }
    }
    /**
     * @internal
     */
    runIfDirty() {
      if (isDirty(this)) {
        this.run();
      }
    }
    get dirty() {
      return isDirty(this);
    }
  };
  var batchDepth = 0;
  var batchedSub;
  var batchedComputed;
  function batch(sub, isComputed = false) {
    sub.flags |= 8;
    if (isComputed) {
      sub.next = batchedComputed;
      batchedComputed = sub;
      return;
    }
    sub.next = batchedSub;
    batchedSub = sub;
  }
  function startBatch() {
    batchDepth++;
  }
  function endBatch() {
    if (--batchDepth > 0) {
      return;
    }
    if (batchedComputed) {
      let e = batchedComputed;
      batchedComputed = void 0;
      while (e) {
        const next = e.next;
        e.next = void 0;
        e.flags &= ~8;
        e = next;
      }
    }
    let error;
    while (batchedSub) {
      let e = batchedSub;
      batchedSub = void 0;
      while (e) {
        const next = e.next;
        e.next = void 0;
        e.flags &= ~8;
        if (e.flags & 1) {
          try {
            ;
            e.trigger();
          } catch (err) {
            if (!error)
              error = err;
          }
        }
        e = next;
      }
    }
    if (error)
      throw error;
  }
  function prepareDeps(sub) {
    for (let link = sub.deps; link; link = link.nextDep) {
      link.version = -1;
      link.prevActiveLink = link.dep.activeLink;
      link.dep.activeLink = link;
    }
  }
  function cleanupDeps(sub) {
    let head;
    let tail = sub.depsTail;
    let link = tail;
    while (link) {
      const prev = link.prevDep;
      if (link.version === -1) {
        if (link === tail)
          tail = prev;
        removeSub(link);
        removeDep(link);
      } else {
        head = link;
      }
      link.dep.activeLink = link.prevActiveLink;
      link.prevActiveLink = void 0;
      link = prev;
    }
    sub.deps = head;
    sub.depsTail = tail;
  }
  function isDirty(sub) {
    for (let link = sub.deps; link; link = link.nextDep) {
      if (link.dep.version !== link.version || link.dep.computed && (refreshComputed(link.dep.computed) || link.dep.version !== link.version)) {
        return true;
      }
    }
    if (sub._dirty) {
      return true;
    }
    return false;
  }
  function refreshComputed(computed3) {
    if (computed3.flags & 4 && !(computed3.flags & 16)) {
      return;
    }
    computed3.flags &= ~16;
    if (computed3.globalVersion === globalVersion) {
      return;
    }
    computed3.globalVersion = globalVersion;
    const dep = computed3.dep;
    computed3.flags |= 2;
    if (dep.version > 0 && !computed3.isSSR && computed3.deps && !isDirty(computed3)) {
      computed3.flags &= ~2;
      return;
    }
    const prevSub = activeSub;
    const prevShouldTrack = shouldTrack;
    activeSub = computed3;
    shouldTrack = true;
    try {
      prepareDeps(computed3);
      const value = computed3.fn(computed3._value);
      if (dep.version === 0 || hasChanged(value, computed3._value)) {
        computed3._value = value;
        dep.version++;
      }
    } catch (err) {
      dep.version++;
      throw err;
    } finally {
      activeSub = prevSub;
      shouldTrack = prevShouldTrack;
      cleanupDeps(computed3);
      computed3.flags &= ~2;
    }
  }
  function removeSub(link, soft = false) {
    const { dep, prevSub, nextSub } = link;
    if (prevSub) {
      prevSub.nextSub = nextSub;
      link.prevSub = void 0;
    }
    if (nextSub) {
      nextSub.prevSub = prevSub;
      link.nextSub = void 0;
    }
    if (dep.subsHead === link) {
      dep.subsHead = nextSub;
    }
    if (dep.subs === link) {
      dep.subs = prevSub;
      if (!prevSub && dep.computed) {
        dep.computed.flags &= ~4;
        for (let l = dep.computed.deps; l; l = l.nextDep) {
          removeSub(l, true);
        }
      }
    }
    if (!soft && !--dep.sc && dep.map) {
      dep.map.delete(dep.key);
    }
  }
  function removeDep(link) {
    const { prevDep, nextDep } = link;
    if (prevDep) {
      prevDep.nextDep = nextDep;
      link.prevDep = void 0;
    }
    if (nextDep) {
      nextDep.prevDep = prevDep;
      link.nextDep = void 0;
    }
  }
  var shouldTrack = true;
  var trackStack = [];
  function pauseTracking() {
    trackStack.push(shouldTrack);
    shouldTrack = false;
  }
  function resetTracking() {
    const last = trackStack.pop();
    shouldTrack = last === void 0 ? true : last;
  }
  function cleanupEffect(e) {
    const { cleanup } = e;
    e.cleanup = void 0;
    if (cleanup) {
      const prevSub = activeSub;
      activeSub = void 0;
      try {
        cleanup();
      } finally {
        activeSub = prevSub;
      }
    }
  }
  var globalVersion = 0;
  var Link = class {
    constructor(sub, dep) {
      this.sub = sub;
      this.dep = dep;
      this.version = dep.version;
      this.nextDep = this.prevDep = this.nextSub = this.prevSub = this.prevActiveLink = void 0;
    }
  };
  var Dep = class {
    constructor(computed3) {
      this.computed = computed3;
      this.version = 0;
      this.activeLink = void 0;
      this.subs = void 0;
      this.map = void 0;
      this.key = void 0;
      this.sc = 0;
      if (true) {
        this.subsHead = void 0;
      }
    }
    track(debugInfo) {
      if (!activeSub || !shouldTrack || activeSub === this.computed) {
        return;
      }
      let link = this.activeLink;
      if (link === void 0 || link.sub !== activeSub) {
        link = this.activeLink = new Link(activeSub, this);
        if (!activeSub.deps) {
          activeSub.deps = activeSub.depsTail = link;
        } else {
          link.prevDep = activeSub.depsTail;
          activeSub.depsTail.nextDep = link;
          activeSub.depsTail = link;
        }
        addSub(link);
      } else if (link.version === -1) {
        link.version = this.version;
        if (link.nextDep) {
          const next = link.nextDep;
          next.prevDep = link.prevDep;
          if (link.prevDep) {
            link.prevDep.nextDep = next;
          }
          link.prevDep = activeSub.depsTail;
          link.nextDep = void 0;
          activeSub.depsTail.nextDep = link;
          activeSub.depsTail = link;
          if (activeSub.deps === link) {
            activeSub.deps = next;
          }
        }
      }
      if (activeSub.onTrack) {
        activeSub.onTrack(
          extend(
            {
              effect: activeSub
            },
            debugInfo
          )
        );
      }
      return link;
    }
    trigger(debugInfo) {
      this.version++;
      globalVersion++;
      this.notify(debugInfo);
    }
    notify(debugInfo) {
      startBatch();
      try {
        if (true) {
          for (let head = this.subsHead; head; head = head.nextSub) {
            if (head.sub.onTrigger && !(head.sub.flags & 8)) {
              head.sub.onTrigger(
                extend(
                  {
                    effect: head.sub
                  },
                  debugInfo
                )
              );
            }
          }
        }
        for (let link = this.subs; link; link = link.prevSub) {
          if (link.sub.notify()) {
            ;
            link.sub.dep.notify();
          }
        }
      } finally {
        endBatch();
      }
    }
  };
  function addSub(link) {
    link.dep.sc++;
    if (link.sub.flags & 4) {
      const computed3 = link.dep.computed;
      if (computed3 && !link.dep.subs) {
        computed3.flags |= 4 | 16;
        for (let l = computed3.deps; l; l = l.nextDep) {
          addSub(l);
        }
      }
      const currentTail = link.dep.subs;
      if (currentTail !== link) {
        link.prevSub = currentTail;
        if (currentTail)
          currentTail.nextSub = link;
      }
      if (link.dep.subsHead === void 0) {
        link.dep.subsHead = link;
      }
      link.dep.subs = link;
    }
  }
  var targetMap = /* @__PURE__ */ new WeakMap();
  var ITERATE_KEY = Symbol(
    true ? "Object iterate" : ""
  );
  var MAP_KEY_ITERATE_KEY = Symbol(
    true ? "Map keys iterate" : ""
  );
  var ARRAY_ITERATE_KEY = Symbol(
    true ? "Array iterate" : ""
  );
  function track(target, type, key) {
    if (shouldTrack && activeSub) {
      let depsMap = targetMap.get(target);
      if (!depsMap) {
        targetMap.set(target, depsMap = /* @__PURE__ */ new Map());
      }
      let dep = depsMap.get(key);
      if (!dep) {
        depsMap.set(key, dep = new Dep());
        dep.map = depsMap;
        dep.key = key;
      }
      if (true) {
        dep.track({
          target,
          type,
          key
        });
      } else {
        dep.track();
      }
    }
  }
  function trigger(target, type, key, newValue, oldValue, oldTarget) {
    const depsMap = targetMap.get(target);
    if (!depsMap) {
      globalVersion++;
      return;
    }
    const run = (dep) => {
      if (dep) {
        if (true) {
          dep.trigger({
            target,
            type,
            key,
            newValue,
            oldValue,
            oldTarget
          });
        } else {
          dep.trigger();
        }
      }
    };
    startBatch();
    if (type === "clear") {
      depsMap.forEach(run);
    } else {
      const targetIsArray = isArray(target);
      const isArrayIndex = targetIsArray && isIntegerKey(key);
      if (targetIsArray && key === "length") {
        const newLength = Number(newValue);
        depsMap.forEach((dep, key2) => {
          if (key2 === "length" || key2 === ARRAY_ITERATE_KEY || !isSymbol(key2) && key2 >= newLength) {
            run(dep);
          }
        });
      } else {
        if (key !== void 0 || depsMap.has(void 0)) {
          run(depsMap.get(key));
        }
        if (isArrayIndex) {
          run(depsMap.get(ARRAY_ITERATE_KEY));
        }
        switch (type) {
          case "add":
            if (!targetIsArray) {
              run(depsMap.get(ITERATE_KEY));
              if (isMap(target)) {
                run(depsMap.get(MAP_KEY_ITERATE_KEY));
              }
            } else if (isArrayIndex) {
              run(depsMap.get("length"));
            }
            break;
          case "delete":
            if (!targetIsArray) {
              run(depsMap.get(ITERATE_KEY));
              if (isMap(target)) {
                run(depsMap.get(MAP_KEY_ITERATE_KEY));
              }
            }
            break;
          case "set":
            if (isMap(target)) {
              run(depsMap.get(ITERATE_KEY));
            }
            break;
        }
      }
    }
    endBatch();
  }
  function reactiveReadArray(array) {
    const raw = toRaw(array);
    if (raw === array)
      return raw;
    track(raw, "iterate", ARRAY_ITERATE_KEY);
    return isShallow(array) ? raw : raw.map(toReactive);
  }
  function shallowReadArray(arr) {
    track(arr = toRaw(arr), "iterate", ARRAY_ITERATE_KEY);
    return arr;
  }
  var arrayInstrumentations = {
    __proto__: null,
    [Symbol.iterator]() {
      return iterator(this, Symbol.iterator, toReactive);
    },
    concat(...args) {
      return reactiveReadArray(this).concat(
        ...args.map((x) => isArray(x) ? reactiveReadArray(x) : x)
      );
    },
    entries() {
      return iterator(this, "entries", (value) => {
        value[1] = toReactive(value[1]);
        return value;
      });
    },
    every(fn, thisArg) {
      return apply(this, "every", fn, thisArg, void 0, arguments);
    },
    filter(fn, thisArg) {
      return apply(this, "filter", fn, thisArg, (v) => v.map(toReactive), arguments);
    },
    find(fn, thisArg) {
      return apply(this, "find", fn, thisArg, toReactive, arguments);
    },
    findIndex(fn, thisArg) {
      return apply(this, "findIndex", fn, thisArg, void 0, arguments);
    },
    findLast(fn, thisArg) {
      return apply(this, "findLast", fn, thisArg, toReactive, arguments);
    },
    findLastIndex(fn, thisArg) {
      return apply(this, "findLastIndex", fn, thisArg, void 0, arguments);
    },
    // flat, flatMap could benefit from ARRAY_ITERATE but are not straight-forward to implement
    forEach(fn, thisArg) {
      return apply(this, "forEach", fn, thisArg, void 0, arguments);
    },
    includes(...args) {
      return searchProxy(this, "includes", args);
    },
    indexOf(...args) {
      return searchProxy(this, "indexOf", args);
    },
    join(separator) {
      return reactiveReadArray(this).join(separator);
    },
    // keys() iterator only reads `length`, no optimisation required
    lastIndexOf(...args) {
      return searchProxy(this, "lastIndexOf", args);
    },
    map(fn, thisArg) {
      return apply(this, "map", fn, thisArg, void 0, arguments);
    },
    pop() {
      return noTracking(this, "pop");
    },
    push(...args) {
      return noTracking(this, "push", args);
    },
    reduce(fn, ...args) {
      return reduce(this, "reduce", fn, args);
    },
    reduceRight(fn, ...args) {
      return reduce(this, "reduceRight", fn, args);
    },
    shift() {
      return noTracking(this, "shift");
    },
    // slice could use ARRAY_ITERATE but also seems to beg for range tracking
    some(fn, thisArg) {
      return apply(this, "some", fn, thisArg, void 0, arguments);
    },
    splice(...args) {
      return noTracking(this, "splice", args);
    },
    toReversed() {
      return reactiveReadArray(this).toReversed();
    },
    toSorted(comparer) {
      return reactiveReadArray(this).toSorted(comparer);
    },
    toSpliced(...args) {
      return reactiveReadArray(this).toSpliced(...args);
    },
    unshift(...args) {
      return noTracking(this, "unshift", args);
    },
    values() {
      return iterator(this, "values", toReactive);
    }
  };
  function iterator(self2, method, wrapValue) {
    const arr = shallowReadArray(self2);
    const iter = arr[method]();
    if (arr !== self2 && !isShallow(self2)) {
      iter._next = iter.next;
      iter.next = () => {
        const result = iter._next();
        if (result.value) {
          result.value = wrapValue(result.value);
        }
        return result;
      };
    }
    return iter;
  }
  var arrayProto = Array.prototype;
  function apply(self2, method, fn, thisArg, wrappedRetFn, args) {
    const arr = shallowReadArray(self2);
    const needsWrap = arr !== self2 && !isShallow(self2);
    const methodFn = arr[method];
    if (methodFn !== arrayProto[method]) {
      const result2 = methodFn.apply(self2, args);
      return needsWrap ? toReactive(result2) : result2;
    }
    let wrappedFn = fn;
    if (arr !== self2) {
      if (needsWrap) {
        wrappedFn = function(item, index) {
          return fn.call(this, toReactive(item), index, self2);
        };
      } else if (fn.length > 2) {
        wrappedFn = function(item, index) {
          return fn.call(this, item, index, self2);
        };
      }
    }
    const result = methodFn.call(arr, wrappedFn, thisArg);
    return needsWrap && wrappedRetFn ? wrappedRetFn(result) : result;
  }
  function reduce(self2, method, fn, args) {
    const arr = shallowReadArray(self2);
    let wrappedFn = fn;
    if (arr !== self2) {
      if (!isShallow(self2)) {
        wrappedFn = function(acc, item, index) {
          return fn.call(this, acc, toReactive(item), index, self2);
        };
      } else if (fn.length > 3) {
        wrappedFn = function(acc, item, index) {
          return fn.call(this, acc, item, index, self2);
        };
      }
    }
    return arr[method](wrappedFn, ...args);
  }
  function searchProxy(self2, method, args) {
    const arr = toRaw(self2);
    track(arr, "iterate", ARRAY_ITERATE_KEY);
    const res = arr[method](...args);
    if ((res === -1 || res === false) && isProxy(args[0])) {
      args[0] = toRaw(args[0]);
      return arr[method](...args);
    }
    return res;
  }
  function noTracking(self2, method, args = []) {
    pauseTracking();
    startBatch();
    const res = toRaw(self2)[method].apply(self2, args);
    endBatch();
    resetTracking();
    return res;
  }
  var isNonTrackableKeys = /* @__PURE__ */ makeMap(`__proto__,__v_isRef,__isVue`);
  var builtInSymbols = new Set(
    /* @__PURE__ */ Object.getOwnPropertyNames(Symbol).filter((key) => key !== "arguments" && key !== "caller").map((key) => Symbol[key]).filter(isSymbol)
  );
  function hasOwnProperty2(key) {
    if (!isSymbol(key))
      key = String(key);
    const obj = toRaw(this);
    track(obj, "has", key);
    return obj.hasOwnProperty(key);
  }
  var BaseReactiveHandler = class {
    constructor(_isReadonly = false, _isShallow = false) {
      this._isReadonly = _isReadonly;
      this._isShallow = _isShallow;
    }
    get(target, key, receiver) {
      if (key === "__v_skip")
        return target["__v_skip"];
      const isReadonly2 = this._isReadonly, isShallow2 = this._isShallow;
      if (key === "__v_isReactive") {
        return !isReadonly2;
      } else if (key === "__v_isReadonly") {
        return isReadonly2;
      } else if (key === "__v_isShallow") {
        return isShallow2;
      } else if (key === "__v_raw") {
        if (receiver === (isReadonly2 ? isShallow2 ? shallowReadonlyMap : readonlyMap : isShallow2 ? shallowReactiveMap : reactiveMap).get(target) || // receiver is not the reactive proxy, but has the same prototype
        // this means the receiver is a user proxy of the reactive proxy
        Object.getPrototypeOf(target) === Object.getPrototypeOf(receiver)) {
          return target;
        }
        return;
      }
      const targetIsArray = isArray(target);
      if (!isReadonly2) {
        let fn;
        if (targetIsArray && (fn = arrayInstrumentations[key])) {
          return fn;
        }
        if (key === "hasOwnProperty") {
          return hasOwnProperty2;
        }
      }
      const res = Reflect.get(
        target,
        key,
        // if this is a proxy wrapping a ref, return methods using the raw ref
        // as receiver so that we don't have to call `toRaw` on the ref in all
        // its class methods
        isRef2(target) ? target : receiver
      );
      if (isSymbol(key) ? builtInSymbols.has(key) : isNonTrackableKeys(key)) {
        return res;
      }
      if (!isReadonly2) {
        track(target, "get", key);
      }
      if (isShallow2) {
        return res;
      }
      if (isRef2(res)) {
        return targetIsArray && isIntegerKey(key) ? res : res.value;
      }
      if (isObject(res)) {
        return isReadonly2 ? readonly(res) : reactive(res);
      }
      return res;
    }
  };
  var MutableReactiveHandler = class extends BaseReactiveHandler {
    constructor(isShallow2 = false) {
      super(false, isShallow2);
    }
    set(target, key, value, receiver) {
      let oldValue = target[key];
      if (!this._isShallow) {
        const isOldValueReadonly = isReadonly(oldValue);
        if (!isShallow(value) && !isReadonly(value)) {
          oldValue = toRaw(oldValue);
          value = toRaw(value);
        }
        if (!isArray(target) && isRef2(oldValue) && !isRef2(value)) {
          if (isOldValueReadonly) {
            return false;
          } else {
            oldValue.value = value;
            return true;
          }
        }
      }
      const hadKey = isArray(target) && isIntegerKey(key) ? Number(key) < target.length : hasOwn(target, key);
      const result = Reflect.set(
        target,
        key,
        value,
        isRef2(target) ? target : receiver
      );
      if (target === toRaw(receiver)) {
        if (!hadKey) {
          trigger(target, "add", key, value);
        } else if (hasChanged(value, oldValue)) {
          trigger(target, "set", key, value, oldValue);
        }
      }
      return result;
    }
    deleteProperty(target, key) {
      const hadKey = hasOwn(target, key);
      const oldValue = target[key];
      const result = Reflect.deleteProperty(target, key);
      if (result && hadKey) {
        trigger(target, "delete", key, void 0, oldValue);
      }
      return result;
    }
    has(target, key) {
      const result = Reflect.has(target, key);
      if (!isSymbol(key) || !builtInSymbols.has(key)) {
        track(target, "has", key);
      }
      return result;
    }
    ownKeys(target) {
      track(
        target,
        "iterate",
        isArray(target) ? "length" : ITERATE_KEY
      );
      return Reflect.ownKeys(target);
    }
  };
  var ReadonlyReactiveHandler = class extends BaseReactiveHandler {
    constructor(isShallow2 = false) {
      super(true, isShallow2);
    }
    set(target, key) {
      if (true) {
        warn(
          `Set operation on key "${String(key)}" failed: target is readonly.`,
          target
        );
      }
      return true;
    }
    deleteProperty(target, key) {
      if (true) {
        warn(
          `Delete operation on key "${String(key)}" failed: target is readonly.`,
          target
        );
      }
      return true;
    }
  };
  var mutableHandlers = /* @__PURE__ */ new MutableReactiveHandler();
  var readonlyHandlers = /* @__PURE__ */ new ReadonlyReactiveHandler();
  var shallowReactiveHandlers = /* @__PURE__ */ new MutableReactiveHandler(true);
  var shallowReadonlyHandlers = /* @__PURE__ */ new ReadonlyReactiveHandler(true);
  var toShallow = (value) => value;
  var getProto = (v) => Reflect.getPrototypeOf(v);
  function createIterableMethod(method, isReadonly2, isShallow2) {
    return function(...args) {
      const target = this["__v_raw"];
      const rawTarget = toRaw(target);
      const targetIsMap = isMap(rawTarget);
      const isPair = method === "entries" || method === Symbol.iterator && targetIsMap;
      const isKeyOnly = method === "keys" && targetIsMap;
      const innerIterator = target[method](...args);
      const wrap = isShallow2 ? toShallow : isReadonly2 ? toReadonly : toReactive;
      !isReadonly2 && track(
        rawTarget,
        "iterate",
        isKeyOnly ? MAP_KEY_ITERATE_KEY : ITERATE_KEY
      );
      return {
        // iterator protocol
        next() {
          const { value, done } = innerIterator.next();
          return done ? { value, done } : {
            value: isPair ? [wrap(value[0]), wrap(value[1])] : wrap(value),
            done
          };
        },
        // iterable protocol
        [Symbol.iterator]() {
          return this;
        }
      };
    };
  }
  function createReadonlyMethod(type) {
    return function(...args) {
      if (true) {
        const key = args[0] ? `on key "${args[0]}" ` : ``;
        warn(
          `${capitalize(type)} operation ${key}failed: target is readonly.`,
          toRaw(this)
        );
      }
      return type === "delete" ? false : type === "clear" ? void 0 : this;
    };
  }
  function createInstrumentations(readonly2, shallow) {
    const instrumentations = {
      get(key) {
        const target = this["__v_raw"];
        const rawTarget = toRaw(target);
        const rawKey = toRaw(key);
        if (!readonly2) {
          if (hasChanged(key, rawKey)) {
            track(rawTarget, "get", key);
          }
          track(rawTarget, "get", rawKey);
        }
        const { has } = getProto(rawTarget);
        const wrap = shallow ? toShallow : readonly2 ? toReadonly : toReactive;
        if (has.call(rawTarget, key)) {
          return wrap(target.get(key));
        } else if (has.call(rawTarget, rawKey)) {
          return wrap(target.get(rawKey));
        } else if (target !== rawTarget) {
          target.get(key);
        }
      },
      get size() {
        const target = this["__v_raw"];
        !readonly2 && track(toRaw(target), "iterate", ITERATE_KEY);
        return Reflect.get(target, "size", target);
      },
      has(key) {
        const target = this["__v_raw"];
        const rawTarget = toRaw(target);
        const rawKey = toRaw(key);
        if (!readonly2) {
          if (hasChanged(key, rawKey)) {
            track(rawTarget, "has", key);
          }
          track(rawTarget, "has", rawKey);
        }
        return key === rawKey ? target.has(key) : target.has(key) || target.has(rawKey);
      },
      forEach(callback, thisArg) {
        const observed = this;
        const target = observed["__v_raw"];
        const rawTarget = toRaw(target);
        const wrap = shallow ? toShallow : readonly2 ? toReadonly : toReactive;
        !readonly2 && track(rawTarget, "iterate", ITERATE_KEY);
        return target.forEach((value, key) => {
          return callback.call(thisArg, wrap(value), wrap(key), observed);
        });
      }
    };
    extend(
      instrumentations,
      readonly2 ? {
        add: createReadonlyMethod("add"),
        set: createReadonlyMethod("set"),
        delete: createReadonlyMethod("delete"),
        clear: createReadonlyMethod("clear")
      } : {
        add(value) {
          if (!shallow && !isShallow(value) && !isReadonly(value)) {
            value = toRaw(value);
          }
          const target = toRaw(this);
          const proto = getProto(target);
          const hadKey = proto.has.call(target, value);
          if (!hadKey) {
            target.add(value);
            trigger(target, "add", value, value);
          }
          return this;
        },
        set(key, value) {
          if (!shallow && !isShallow(value) && !isReadonly(value)) {
            value = toRaw(value);
          }
          const target = toRaw(this);
          const { has, get } = getProto(target);
          let hadKey = has.call(target, key);
          if (!hadKey) {
            key = toRaw(key);
            hadKey = has.call(target, key);
          } else if (true) {
            checkIdentityKeys(target, has, key);
          }
          const oldValue = get.call(target, key);
          target.set(key, value);
          if (!hadKey) {
            trigger(target, "add", key, value);
          } else if (hasChanged(value, oldValue)) {
            trigger(target, "set", key, value, oldValue);
          }
          return this;
        },
        delete(key) {
          const target = toRaw(this);
          const { has, get } = getProto(target);
          let hadKey = has.call(target, key);
          if (!hadKey) {
            key = toRaw(key);
            hadKey = has.call(target, key);
          } else if (true) {
            checkIdentityKeys(target, has, key);
          }
          const oldValue = get ? get.call(target, key) : void 0;
          const result = target.delete(key);
          if (hadKey) {
            trigger(target, "delete", key, void 0, oldValue);
          }
          return result;
        },
        clear() {
          const target = toRaw(this);
          const hadItems = target.size !== 0;
          const oldTarget = true ? isMap(target) ? new Map(target) : new Set(target) : void 0;
          const result = target.clear();
          if (hadItems) {
            trigger(
              target,
              "clear",
              void 0,
              void 0,
              oldTarget
            );
          }
          return result;
        }
      }
    );
    const iteratorMethods = [
      "keys",
      "values",
      "entries",
      Symbol.iterator
    ];
    iteratorMethods.forEach((method) => {
      instrumentations[method] = createIterableMethod(method, readonly2, shallow);
    });
    return instrumentations;
  }
  function createInstrumentationGetter(isReadonly2, shallow) {
    const instrumentations = createInstrumentations(isReadonly2, shallow);
    return (target, key, receiver) => {
      if (key === "__v_isReactive") {
        return !isReadonly2;
      } else if (key === "__v_isReadonly") {
        return isReadonly2;
      } else if (key === "__v_raw") {
        return target;
      }
      return Reflect.get(
        hasOwn(instrumentations, key) && key in target ? instrumentations : target,
        key,
        receiver
      );
    };
  }
  var mutableCollectionHandlers = {
    get: /* @__PURE__ */ createInstrumentationGetter(false, false)
  };
  var shallowCollectionHandlers = {
    get: /* @__PURE__ */ createInstrumentationGetter(false, true)
  };
  var readonlyCollectionHandlers = {
    get: /* @__PURE__ */ createInstrumentationGetter(true, false)
  };
  var shallowReadonlyCollectionHandlers = {
    get: /* @__PURE__ */ createInstrumentationGetter(true, true)
  };
  function checkIdentityKeys(target, has, key) {
    const rawKey = toRaw(key);
    if (rawKey !== key && has.call(target, rawKey)) {
      const type = toRawType(target);
      warn(
        `Reactive ${type} contains both the raw and reactive versions of the same object${type === `Map` ? ` as keys` : ``}, which can lead to inconsistencies. Avoid differentiating between the raw and reactive versions of an object and only use the reactive version if possible.`
      );
    }
  }
  var reactiveMap = /* @__PURE__ */ new WeakMap();
  var shallowReactiveMap = /* @__PURE__ */ new WeakMap();
  var readonlyMap = /* @__PURE__ */ new WeakMap();
  var shallowReadonlyMap = /* @__PURE__ */ new WeakMap();
  function targetTypeMap(rawType) {
    switch (rawType) {
      case "Object":
      case "Array":
        return 1;
      case "Map":
      case "Set":
      case "WeakMap":
      case "WeakSet":
        return 2;
      default:
        return 0;
    }
  }
  function getTargetType(value) {
    return value["__v_skip"] || !Object.isExtensible(value) ? 0 : targetTypeMap(toRawType(value));
  }
  function reactive(target) {
    if (isReadonly(target)) {
      return target;
    }
    return createReactiveObject(
      target,
      false,
      mutableHandlers,
      mutableCollectionHandlers,
      reactiveMap
    );
  }
  function shallowReactive(target) {
    return createReactiveObject(
      target,
      false,
      shallowReactiveHandlers,
      shallowCollectionHandlers,
      shallowReactiveMap
    );
  }
  function readonly(target) {
    return createReactiveObject(
      target,
      true,
      readonlyHandlers,
      readonlyCollectionHandlers,
      readonlyMap
    );
  }
  function shallowReadonly(target) {
    return createReactiveObject(
      target,
      true,
      shallowReadonlyHandlers,
      shallowReadonlyCollectionHandlers,
      shallowReadonlyMap
    );
  }
  function createReactiveObject(target, isReadonly2, baseHandlers, collectionHandlers, proxyMap) {
    if (!isObject(target)) {
      if (true) {
        warn(
          `value cannot be made ${isReadonly2 ? "readonly" : "reactive"}: ${String(
            target
          )}`
        );
      }
      return target;
    }
    if (target["__v_raw"] && !(isReadonly2 && target["__v_isReactive"])) {
      return target;
    }
    const existingProxy = proxyMap.get(target);
    if (existingProxy) {
      return existingProxy;
    }
    const targetType = getTargetType(target);
    if (targetType === 0) {
      return target;
    }
    const proxy = new Proxy(
      target,
      targetType === 2 ? collectionHandlers : baseHandlers
    );
    proxyMap.set(target, proxy);
    return proxy;
  }
  function isReactive(value) {
    if (isReadonly(value)) {
      return isReactive(value["__v_raw"]);
    }
    return !!(value && value["__v_isReactive"]);
  }
  function isReadonly(value) {
    return !!(value && value["__v_isReadonly"]);
  }
  function isShallow(value) {
    return !!(value && value["__v_isShallow"]);
  }
  function isProxy(value) {
    return value ? !!value["__v_raw"] : false;
  }
  function toRaw(observed) {
    const raw = observed && observed["__v_raw"];
    return raw ? toRaw(raw) : observed;
  }
  function markRaw(value) {
    if (!hasOwn(value, "__v_skip") && Object.isExtensible(value)) {
      def(value, "__v_skip", true);
    }
    return value;
  }
  var toReactive = (value) => isObject(value) ? reactive(value) : value;
  var toReadonly = (value) => isObject(value) ? readonly(value) : value;
  function isRef2(r) {
    return r ? r["__v_isRef"] === true : false;
  }
  function ref(value) {
    return createRef(value, false);
  }
  function createRef(rawValue, shallow) {
    if (isRef2(rawValue)) {
      return rawValue;
    }
    return new RefImpl(rawValue, shallow);
  }
  var RefImpl = class {
    constructor(value, isShallow2) {
      this.dep = new Dep();
      this["__v_isRef"] = true;
      this["__v_isShallow"] = false;
      this._rawValue = isShallow2 ? value : toRaw(value);
      this._value = isShallow2 ? value : toReactive(value);
      this["__v_isShallow"] = isShallow2;
    }
    get value() {
      if (true) {
        this.dep.track({
          target: this,
          type: "get",
          key: "value"
        });
      } else {
        this.dep.track();
      }
      return this._value;
    }
    set value(newValue) {
      const oldValue = this._rawValue;
      const useDirectValue = this["__v_isShallow"] || isShallow(newValue) || isReadonly(newValue);
      newValue = useDirectValue ? newValue : toRaw(newValue);
      if (hasChanged(newValue, oldValue)) {
        this._rawValue = newValue;
        this._value = useDirectValue ? newValue : toReactive(newValue);
        if (true) {
          this.dep.trigger({
            target: this,
            type: "set",
            key: "value",
            newValue,
            oldValue
          });
        } else {
          this.dep.trigger();
        }
      }
    }
  };
  function unref(ref2) {
    return isRef2(ref2) ? ref2.value : ref2;
  }
  var shallowUnwrapHandlers = {
    get: (target, key, receiver) => key === "__v_raw" ? target : unref(Reflect.get(target, key, receiver)),
    set: (target, key, value, receiver) => {
      const oldValue = target[key];
      if (isRef2(oldValue) && !isRef2(value)) {
        oldValue.value = value;
        return true;
      } else {
        return Reflect.set(target, key, value, receiver);
      }
    }
  };
  function proxyRefs(objectWithRefs) {
    return isReactive(objectWithRefs) ? objectWithRefs : new Proxy(objectWithRefs, shallowUnwrapHandlers);
  }
  var ComputedRefImpl = class {
    constructor(fn, setter, isSSR) {
      this.fn = fn;
      this.setter = setter;
      this._value = void 0;
      this.dep = new Dep(this);
      this.__v_isRef = true;
      this.deps = void 0;
      this.depsTail = void 0;
      this.flags = 16;
      this.globalVersion = globalVersion - 1;
      this.next = void 0;
      this.effect = this;
      this["__v_isReadonly"] = !setter;
      this.isSSR = isSSR;
    }
    /**
     * @internal
     */
    notify() {
      this.flags |= 16;
      if (!(this.flags & 8) && // avoid infinite self recursion
      activeSub !== this) {
        batch(this, true);
        return true;
      } else if (true)
        ;
    }
    get value() {
      const link = true ? this.dep.track({
        target: this,
        type: "get",
        key: "value"
      }) : this.dep.track();
      refreshComputed(this);
      if (link) {
        link.version = this.dep.version;
      }
      return this._value;
    }
    set value(newValue) {
      if (this.setter) {
        this.setter(newValue);
      } else if (true) {
        warn("Write operation failed: computed value is readonly");
      }
    }
  };
  function computed(getterOrOptions, debugOptions, isSSR = false) {
    let getter;
    let setter;
    if (isFunction(getterOrOptions)) {
      getter = getterOrOptions;
    } else {
      getter = getterOrOptions.get;
      setter = getterOrOptions.set;
    }
    const cRef = new ComputedRefImpl(getter, setter, isSSR);
    if (debugOptions && !isSSR) {
      cRef.onTrack = debugOptions.onTrack;
      cRef.onTrigger = debugOptions.onTrigger;
    }
    return cRef;
  }
  var INITIAL_WATCHER_VALUE = {};
  var cleanupMap = /* @__PURE__ */ new WeakMap();
  var activeWatcher = void 0;
  function onWatcherCleanup(cleanupFn, failSilently = false, owner = activeWatcher) {
    if (owner) {
      let cleanups = cleanupMap.get(owner);
      if (!cleanups)
        cleanupMap.set(owner, cleanups = []);
      cleanups.push(cleanupFn);
    } else if (!failSilently) {
      warn(
        `onWatcherCleanup() was called when there was no active watcher to associate with.`
      );
    }
  }
  function watch(source, cb, options = EMPTY_OBJ) {
    const { immediate, deep, once, scheduler, augmentJob, call } = options;
    const warnInvalidSource = (s) => {
      (options.onWarn || warn)(
        `Invalid watch source: `,
        s,
        `A watch source can only be a getter/effect function, a ref, a reactive object, or an array of these types.`
      );
    };
    const reactiveGetter = (source2) => {
      if (deep)
        return source2;
      if (isShallow(source2) || deep === false || deep === 0)
        return traverse(source2, 1);
      return traverse(source2);
    };
    let effect2;
    let getter;
    let cleanup;
    let boundCleanup;
    let forceTrigger = false;
    let isMultiSource = false;
    if (isRef2(source)) {
      getter = () => source.value;
      forceTrigger = isShallow(source);
    } else if (isReactive(source)) {
      getter = () => reactiveGetter(source);
      forceTrigger = true;
    } else if (isArray(source)) {
      isMultiSource = true;
      forceTrigger = source.some((s) => isReactive(s) || isShallow(s));
      getter = () => source.map((s) => {
        if (isRef2(s)) {
          return s.value;
        } else if (isReactive(s)) {
          return reactiveGetter(s);
        } else if (isFunction(s)) {
          return call ? call(s, 2) : s();
        } else {
          warnInvalidSource(s);
        }
      });
    } else if (isFunction(source)) {
      if (cb) {
        getter = call ? () => call(source, 2) : source;
      } else {
        getter = () => {
          if (cleanup) {
            pauseTracking();
            try {
              cleanup();
            } finally {
              resetTracking();
            }
          }
          const currentEffect = activeWatcher;
          activeWatcher = effect2;
          try {
            return call ? call(source, 3, [boundCleanup]) : source(boundCleanup);
          } finally {
            activeWatcher = currentEffect;
          }
        };
      }
    } else {
      getter = NOOP;
      warnInvalidSource(source);
    }
    if (cb && deep) {
      const baseGetter = getter;
      const depth = deep === true ? Infinity : deep;
      getter = () => traverse(baseGetter(), depth);
    }
    const scope = getCurrentScope();
    const watchHandle = () => {
      effect2.stop();
      if (scope && scope.active) {
        remove(scope.effects, effect2);
      }
    };
    if (once && cb) {
      const _cb = cb;
      cb = (...args) => {
        _cb(...args);
        watchHandle();
      };
    }
    let oldValue = isMultiSource ? new Array(source.length).fill(INITIAL_WATCHER_VALUE) : INITIAL_WATCHER_VALUE;
    const job = (immediateFirstRun) => {
      if (!(effect2.flags & 1) || !effect2.dirty && !immediateFirstRun) {
        return;
      }
      if (cb) {
        const newValue = effect2.run();
        if (deep || forceTrigger || (isMultiSource ? newValue.some((v, i) => hasChanged(v, oldValue[i])) : hasChanged(newValue, oldValue))) {
          if (cleanup) {
            cleanup();
          }
          const currentWatcher = activeWatcher;
          activeWatcher = effect2;
          try {
            const args = [
              newValue,
              // pass undefined as the old value when it's changed for the first time
              oldValue === INITIAL_WATCHER_VALUE ? void 0 : isMultiSource && oldValue[0] === INITIAL_WATCHER_VALUE ? [] : oldValue,
              boundCleanup
            ];
            call ? call(cb, 3, args) : (
              // @ts-expect-error
              cb(...args)
            );
            oldValue = newValue;
          } finally {
            activeWatcher = currentWatcher;
          }
        }
      } else {
        effect2.run();
      }
    };
    if (augmentJob) {
      augmentJob(job);
    }
    effect2 = new ReactiveEffect(getter);
    effect2.scheduler = scheduler ? () => scheduler(job, false) : job;
    boundCleanup = (fn) => onWatcherCleanup(fn, false, effect2);
    cleanup = effect2.onStop = () => {
      const cleanups = cleanupMap.get(effect2);
      if (cleanups) {
        if (call) {
          call(cleanups, 4);
        } else {
          for (const cleanup2 of cleanups)
            cleanup2();
        }
        cleanupMap.delete(effect2);
      }
    };
    if (true) {
      effect2.onTrack = options.onTrack;
      effect2.onTrigger = options.onTrigger;
    }
    if (cb) {
      if (immediate) {
        job(true);
      } else {
        oldValue = effect2.run();
      }
    } else if (scheduler) {
      scheduler(job.bind(null, true), true);
    } else {
      effect2.run();
    }
    watchHandle.pause = effect2.pause.bind(effect2);
    watchHandle.resume = effect2.resume.bind(effect2);
    watchHandle.stop = watchHandle;
    return watchHandle;
  }
  function traverse(value, depth = Infinity, seen) {
    if (depth <= 0 || !isObject(value) || value["__v_skip"]) {
      return value;
    }
    seen = seen || /* @__PURE__ */ new Set();
    if (seen.has(value)) {
      return value;
    }
    seen.add(value);
    depth--;
    if (isRef2(value)) {
      traverse(value.value, depth, seen);
    } else if (isArray(value)) {
      for (let i = 0; i < value.length; i++) {
        traverse(value[i], depth, seen);
      }
    } else if (isSet(value) || isMap(value)) {
      value.forEach((v) => {
        traverse(v, depth, seen);
      });
    } else if (isPlainObject(value)) {
      for (const key in value) {
        traverse(value[key], depth, seen);
      }
      for (const key of Object.getOwnPropertySymbols(value)) {
        if (Object.prototype.propertyIsEnumerable.call(value, key)) {
          traverse(value[key], depth, seen);
        }
      }
    }
    return value;
  }

  // node_modules/@vue/runtime-core/dist/runtime-core.esm-bundler.js
  var stack = [];
  function pushWarningContext(vnode) {
    stack.push(vnode);
  }
  function popWarningContext() {
    stack.pop();
  }
  var isWarning = false;
  function warn$1(msg, ...args) {
    if (isWarning)
      return;
    isWarning = true;
    pauseTracking();
    const instance = stack.length ? stack[stack.length - 1].component : null;
    const appWarnHandler = instance && instance.appContext.config.warnHandler;
    const trace = getComponentTrace();
    if (appWarnHandler) {
      callWithErrorHandling(
        appWarnHandler,
        instance,
        11,
        [
          // eslint-disable-next-line no-restricted-syntax
          msg + args.map((a) => {
            var _a, _b;
            return (_b = (_a = a.toString) == null ? void 0 : _a.call(a)) != null ? _b : JSON.stringify(a);
          }).join(""),
          instance && instance.proxy,
          trace.map(
            ({ vnode }) => `at <${formatComponentName(instance, vnode.type)}>`
          ).join("\n"),
          trace
        ]
      );
    } else {
      const warnArgs = [`[Vue warn]: ${msg}`, ...args];
      if (trace.length && // avoid spamming console during tests
      true) {
        warnArgs.push(`
`, ...formatTrace(trace));
      }
      console.warn(...warnArgs);
    }
    resetTracking();
    isWarning = false;
  }
  function getComponentTrace() {
    let currentVNode = stack[stack.length - 1];
    if (!currentVNode) {
      return [];
    }
    const normalizedStack = [];
    while (currentVNode) {
      const last = normalizedStack[0];
      if (last && last.vnode === currentVNode) {
        last.recurseCount++;
      } else {
        normalizedStack.push({
          vnode: currentVNode,
          recurseCount: 0
        });
      }
      const parentInstance = currentVNode.component && currentVNode.component.parent;
      currentVNode = parentInstance && parentInstance.vnode;
    }
    return normalizedStack;
  }
  function formatTrace(trace) {
    const logs = [];
    trace.forEach((entry, i) => {
      logs.push(...i === 0 ? [] : [`
`], ...formatTraceEntry(entry));
    });
    return logs;
  }
  function formatTraceEntry({ vnode, recurseCount }) {
    const postfix = recurseCount > 0 ? `... (${recurseCount} recursive calls)` : ``;
    const isRoot = vnode.component ? vnode.component.parent == null : false;
    const open = ` at <${formatComponentName(
      vnode.component,
      vnode.type,
      isRoot
    )}`;
    const close = `>` + postfix;
    return vnode.props ? [open, ...formatProps(vnode.props), close] : [open + close];
  }
  function formatProps(props) {
    const res = [];
    const keys = Object.keys(props);
    keys.slice(0, 3).forEach((key) => {
      res.push(...formatProp(key, props[key]));
    });
    if (keys.length > 3) {
      res.push(` ...`);
    }
    return res;
  }
  function formatProp(key, value, raw) {
    if (isString(value)) {
      value = JSON.stringify(value);
      return raw ? value : [`${key}=${value}`];
    } else if (typeof value === "number" || typeof value === "boolean" || value == null) {
      return raw ? value : [`${key}=${value}`];
    } else if (isRef2(value)) {
      value = formatProp(key, toRaw(value.value), true);
      return raw ? value : [`${key}=Ref<`, value, `>`];
    } else if (isFunction(value)) {
      return [`${key}=fn${value.name ? `<${value.name}>` : ``}`];
    } else {
      value = toRaw(value);
      return raw ? value : [`${key}=`, value];
    }
  }
  var ErrorTypeStrings$1 = {
    ["sp"]: "serverPrefetch hook",
    ["bc"]: "beforeCreate hook",
    ["c"]: "created hook",
    ["bm"]: "beforeMount hook",
    ["m"]: "mounted hook",
    ["bu"]: "beforeUpdate hook",
    ["u"]: "updated",
    ["bum"]: "beforeUnmount hook",
    ["um"]: "unmounted hook",
    ["a"]: "activated hook",
    ["da"]: "deactivated hook",
    ["ec"]: "errorCaptured hook",
    ["rtc"]: "renderTracked hook",
    ["rtg"]: "renderTriggered hook",
    [0]: "setup function",
    [1]: "render function",
    [2]: "watcher getter",
    [3]: "watcher callback",
    [4]: "watcher cleanup function",
    [5]: "native event handler",
    [6]: "component event handler",
    [7]: "vnode hook",
    [8]: "directive hook",
    [9]: "transition hook",
    [10]: "app errorHandler",
    [11]: "app warnHandler",
    [12]: "ref function",
    [13]: "async component loader",
    [14]: "scheduler flush",
    [15]: "component update",
    [16]: "app unmount cleanup function"
  };
  function callWithErrorHandling(fn, instance, type, args) {
    try {
      return args ? fn(...args) : fn();
    } catch (err) {
      handleError(err, instance, type);
    }
  }
  function callWithAsyncErrorHandling(fn, instance, type, args) {
    if (isFunction(fn)) {
      const res = callWithErrorHandling(fn, instance, type, args);
      if (res && isPromise(res)) {
        res.catch((err) => {
          handleError(err, instance, type);
        });
      }
      return res;
    }
    if (isArray(fn)) {
      const values = [];
      for (let i = 0; i < fn.length; i++) {
        values.push(callWithAsyncErrorHandling(fn[i], instance, type, args));
      }
      return values;
    } else if (true) {
      warn$1(
        `Invalid value type passed to callWithAsyncErrorHandling(): ${typeof fn}`
      );
    }
  }
  function handleError(err, instance, type, throwInDev = true) {
    const contextVNode = instance ? instance.vnode : null;
    const { errorHandler, throwUnhandledErrorInProduction } = instance && instance.appContext.config || EMPTY_OBJ;
    if (instance) {
      let cur = instance.parent;
      const exposedInstance = instance.proxy;
      const errorInfo = true ? ErrorTypeStrings$1[type] : `https://vuejs.org/error-reference/#runtime-${type}`;
      while (cur) {
        const errorCapturedHooks = cur.ec;
        if (errorCapturedHooks) {
          for (let i = 0; i < errorCapturedHooks.length; i++) {
            if (errorCapturedHooks[i](err, exposedInstance, errorInfo) === false) {
              return;
            }
          }
        }
        cur = cur.parent;
      }
      if (errorHandler) {
        pauseTracking();
        callWithErrorHandling(errorHandler, null, 10, [
          err,
          exposedInstance,
          errorInfo
        ]);
        resetTracking();
        return;
      }
    }
    logError(err, type, contextVNode, throwInDev, throwUnhandledErrorInProduction);
  }
  function logError(err, type, contextVNode, throwInDev = true, throwInProd = false) {
    if (true) {
      const info = ErrorTypeStrings$1[type];
      if (contextVNode) {
        pushWarningContext(contextVNode);
      }
      warn$1(`Unhandled error${info ? ` during execution of ${info}` : ``}`);
      if (contextVNode) {
        popWarningContext();
      }
      if (throwInDev) {
        throw err;
      } else {
        console.error(err);
      }
    } else if (throwInProd) {
      throw err;
    } else {
      console.error(err);
    }
  }
  var queue = [];
  var flushIndex = -1;
  var pendingPostFlushCbs = [];
  var activePostFlushCbs = null;
  var postFlushIndex = 0;
  var resolvedPromise = /* @__PURE__ */ Promise.resolve();
  var currentFlushPromise = null;
  var RECURSION_LIMIT = 100;
  function nextTick(fn) {
    const p2 = currentFlushPromise || resolvedPromise;
    return fn ? p2.then(this ? fn.bind(this) : fn) : p2;
  }
  function findInsertionIndex(id) {
    let start = flushIndex + 1;
    let end = queue.length;
    while (start < end) {
      const middle = start + end >>> 1;
      const middleJob = queue[middle];
      const middleJobId = getId(middleJob);
      if (middleJobId < id || middleJobId === id && middleJob.flags & 2) {
        start = middle + 1;
      } else {
        end = middle;
      }
    }
    return start;
  }
  function queueJob(job) {
    if (!(job.flags & 1)) {
      const jobId = getId(job);
      const lastJob = queue[queue.length - 1];
      if (!lastJob || // fast path when the job id is larger than the tail
      !(job.flags & 2) && jobId >= getId(lastJob)) {
        queue.push(job);
      } else {
        queue.splice(findInsertionIndex(jobId), 0, job);
      }
      job.flags |= 1;
      queueFlush();
    }
  }
  function queueFlush() {
    if (!currentFlushPromise) {
      currentFlushPromise = resolvedPromise.then(flushJobs);
    }
  }
  function queuePostFlushCb(cb) {
    if (!isArray(cb)) {
      if (activePostFlushCbs && cb.id === -1) {
        activePostFlushCbs.splice(postFlushIndex + 1, 0, cb);
      } else if (!(cb.flags & 1)) {
        pendingPostFlushCbs.push(cb);
        cb.flags |= 1;
      }
    } else {
      pendingPostFlushCbs.push(...cb);
    }
    queueFlush();
  }
  function flushPreFlushCbs(instance, seen, i = flushIndex + 1) {
    if (true) {
      seen = seen || /* @__PURE__ */ new Map();
    }
    for (; i < queue.length; i++) {
      const cb = queue[i];
      if (cb && cb.flags & 2) {
        if (instance && cb.id !== instance.uid) {
          continue;
        }
        if (checkRecursiveUpdates(seen, cb)) {
          continue;
        }
        queue.splice(i, 1);
        i--;
        if (cb.flags & 4) {
          cb.flags &= ~1;
        }
        cb();
        if (!(cb.flags & 4)) {
          cb.flags &= ~1;
        }
      }
    }
  }
  function flushPostFlushCbs(seen) {
    if (pendingPostFlushCbs.length) {
      const deduped = [...new Set(pendingPostFlushCbs)].sort(
        (a, b) => getId(a) - getId(b)
      );
      pendingPostFlushCbs.length = 0;
      if (activePostFlushCbs) {
        activePostFlushCbs.push(...deduped);
        return;
      }
      activePostFlushCbs = deduped;
      if (true) {
        seen = seen || /* @__PURE__ */ new Map();
      }
      for (postFlushIndex = 0; postFlushIndex < activePostFlushCbs.length; postFlushIndex++) {
        const cb = activePostFlushCbs[postFlushIndex];
        if (checkRecursiveUpdates(seen, cb)) {
          continue;
        }
        if (cb.flags & 4) {
          cb.flags &= ~1;
        }
        if (!(cb.flags & 8))
          cb();
        cb.flags &= ~1;
      }
      activePostFlushCbs = null;
      postFlushIndex = 0;
    }
  }
  var getId = (job) => job.id == null ? job.flags & 2 ? -1 : Infinity : job.id;
  function flushJobs(seen) {
    if (true) {
      seen = seen || /* @__PURE__ */ new Map();
    }
    const check = true ? (job) => checkRecursiveUpdates(seen, job) : NOOP;
    try {
      for (flushIndex = 0; flushIndex < queue.length; flushIndex++) {
        const job = queue[flushIndex];
        if (job && !(job.flags & 8)) {
          if (check(job)) {
            continue;
          }
          if (job.flags & 4) {
            job.flags &= ~1;
          }
          callWithErrorHandling(
            job,
            job.i,
            job.i ? 15 : 14
          );
          if (!(job.flags & 4)) {
            job.flags &= ~1;
          }
        }
      }
    } finally {
      for (; flushIndex < queue.length; flushIndex++) {
        const job = queue[flushIndex];
        if (job) {
          job.flags &= ~1;
        }
      }
      flushIndex = -1;
      queue.length = 0;
      flushPostFlushCbs(seen);
      currentFlushPromise = null;
      if (queue.length || pendingPostFlushCbs.length) {
        flushJobs(seen);
      }
    }
  }
  function checkRecursiveUpdates(seen, fn) {
    const count = seen.get(fn) || 0;
    if (count > RECURSION_LIMIT) {
      const instance = fn.i;
      const componentName = instance && getComponentName(instance.type);
      handleError(
        `Maximum recursive updates exceeded${componentName ? ` in component <${componentName}>` : ``}. This means you have a reactive effect that is mutating its own dependencies and thus recursively triggering itself. Possible sources include component template, render function, updated hook or watcher source function.`,
        null,
        10
      );
      return true;
    }
    seen.set(fn, count + 1);
    return false;
  }
  var isHmrUpdating = false;
  var hmrDirtyComponents = /* @__PURE__ */ new Map();
  if (true) {
    getGlobalThis().__VUE_HMR_RUNTIME__ = {
      createRecord: tryWrap(createRecord),
      rerender: tryWrap(rerender),
      reload: tryWrap(reload)
    };
  }
  var map = /* @__PURE__ */ new Map();
  function registerHMR(instance) {
    const id = instance.type.__hmrId;
    let record = map.get(id);
    if (!record) {
      createRecord(id, instance.type);
      record = map.get(id);
    }
    record.instances.add(instance);
  }
  function unregisterHMR(instance) {
    map.get(instance.type.__hmrId).instances.delete(instance);
  }
  function createRecord(id, initialDef) {
    if (map.has(id)) {
      return false;
    }
    map.set(id, {
      initialDef: normalizeClassComponent(initialDef),
      instances: /* @__PURE__ */ new Set()
    });
    return true;
  }
  function normalizeClassComponent(component) {
    return isClassComponent(component) ? component.__vccOpts : component;
  }
  function rerender(id, newRender) {
    const record = map.get(id);
    if (!record) {
      return;
    }
    record.initialDef.render = newRender;
    [...record.instances].forEach((instance) => {
      if (newRender) {
        instance.render = newRender;
        normalizeClassComponent(instance.type).render = newRender;
      }
      instance.renderCache = [];
      isHmrUpdating = true;
      instance.update();
      isHmrUpdating = false;
    });
  }
  function reload(id, newComp) {
    const record = map.get(id);
    if (!record)
      return;
    newComp = normalizeClassComponent(newComp);
    updateComponentDef(record.initialDef, newComp);
    const instances = [...record.instances];
    for (let i = 0; i < instances.length; i++) {
      const instance = instances[i];
      const oldComp = normalizeClassComponent(instance.type);
      let dirtyInstances = hmrDirtyComponents.get(oldComp);
      if (!dirtyInstances) {
        if (oldComp !== record.initialDef) {
          updateComponentDef(oldComp, newComp);
        }
        hmrDirtyComponents.set(oldComp, dirtyInstances = /* @__PURE__ */ new Set());
      }
      dirtyInstances.add(instance);
      instance.appContext.propsCache.delete(instance.type);
      instance.appContext.emitsCache.delete(instance.type);
      instance.appContext.optionsCache.delete(instance.type);
      if (instance.ceReload) {
        dirtyInstances.add(instance);
        instance.ceReload(newComp.styles);
        dirtyInstances.delete(instance);
      } else if (instance.parent) {
        queueJob(() => {
          isHmrUpdating = true;
          instance.parent.update();
          isHmrUpdating = false;
          dirtyInstances.delete(instance);
        });
      } else if (instance.appContext.reload) {
        instance.appContext.reload();
      } else if (typeof window !== "undefined") {
        window.location.reload();
      } else {
        console.warn(
          "[HMR] Root or manually mounted instance modified. Full reload required."
        );
      }
      if (instance.root.ce && instance !== instance.root) {
        instance.root.ce._removeChildStyle(oldComp);
      }
    }
    queuePostFlushCb(() => {
      hmrDirtyComponents.clear();
    });
  }
  function updateComponentDef(oldComp, newComp) {
    extend(oldComp, newComp);
    for (const key in oldComp) {
      if (key !== "__file" && !(key in newComp)) {
        delete oldComp[key];
      }
    }
  }
  function tryWrap(fn) {
    return (id, arg) => {
      try {
        return fn(id, arg);
      } catch (e) {
        console.error(e);
        console.warn(
          `[HMR] Something went wrong during Vue component hot-reload. Full reload required.`
        );
      }
    };
  }
  var devtools$1;
  var buffer = [];
  var devtoolsNotInstalled = false;
  function emit$1(event, ...args) {
    if (devtools$1) {
      devtools$1.emit(event, ...args);
    } else if (!devtoolsNotInstalled) {
      buffer.push({ event, args });
    }
  }
  function setDevtoolsHook$1(hook, target) {
    var _a, _b;
    devtools$1 = hook;
    if (devtools$1) {
      devtools$1.enabled = true;
      buffer.forEach(({ event, args }) => devtools$1.emit(event, ...args));
      buffer = [];
    } else if (
      // handle late devtools injection - only do this if we are in an actual
      // browser environment to avoid the timer handle stalling test runner exit
      // (#4815)
      typeof window !== "undefined" && // some envs mock window but not fully
      window.HTMLElement && // also exclude jsdom
      // eslint-disable-next-line no-restricted-syntax
      !((_b = (_a = window.navigator) == null ? void 0 : _a.userAgent) == null ? void 0 : _b.includes("jsdom"))
    ) {
      const replay = target.__VUE_DEVTOOLS_HOOK_REPLAY__ = target.__VUE_DEVTOOLS_HOOK_REPLAY__ || [];
      replay.push((newHook) => {
        setDevtoolsHook$1(newHook, target);
      });
      setTimeout(() => {
        if (!devtools$1) {
          target.__VUE_DEVTOOLS_HOOK_REPLAY__ = null;
          devtoolsNotInstalled = true;
          buffer = [];
        }
      }, 3e3);
    } else {
      devtoolsNotInstalled = true;
      buffer = [];
    }
  }
  function devtoolsInitApp(app2, version2) {
    emit$1("app:init", app2, version2, {
      Fragment,
      Text,
      Comment,
      Static
    });
  }
  function devtoolsUnmountApp(app2) {
    emit$1("app:unmount", app2);
  }
  var devtoolsComponentAdded = /* @__PURE__ */ createDevtoolsComponentHook(
    "component:added"
    /* COMPONENT_ADDED */
  );
  var devtoolsComponentUpdated = /* @__PURE__ */ createDevtoolsComponentHook(
    "component:updated"
    /* COMPONENT_UPDATED */
  );
  var _devtoolsComponentRemoved = /* @__PURE__ */ createDevtoolsComponentHook(
    "component:removed"
    /* COMPONENT_REMOVED */
  );
  var devtoolsComponentRemoved = (component) => {
    if (devtools$1 && typeof devtools$1.cleanupBuffer === "function" && // remove the component if it wasn't buffered
    !devtools$1.cleanupBuffer(component)) {
      _devtoolsComponentRemoved(component);
    }
  };
  // @__NO_SIDE_EFFECTS__
  function createDevtoolsComponentHook(hook) {
    return (component) => {
      emit$1(
        hook,
        component.appContext.app,
        component.uid,
        component.parent ? component.parent.uid : void 0,
        component
      );
    };
  }
  var devtoolsPerfStart = /* @__PURE__ */ createDevtoolsPerformanceHook(
    "perf:start"
    /* PERFORMANCE_START */
  );
  var devtoolsPerfEnd = /* @__PURE__ */ createDevtoolsPerformanceHook(
    "perf:end"
    /* PERFORMANCE_END */
  );
  function createDevtoolsPerformanceHook(hook) {
    return (component, type, time) => {
      emit$1(hook, component.appContext.app, component.uid, component, type, time);
    };
  }
  function devtoolsComponentEmit(component, event, params) {
    emit$1(
      "component:emit",
      component.appContext.app,
      component,
      event,
      params
    );
  }
  var currentRenderingInstance = null;
  var currentScopeId = null;
  function setCurrentRenderingInstance(instance) {
    const prev = currentRenderingInstance;
    currentRenderingInstance = instance;
    currentScopeId = instance && instance.type.__scopeId || null;
    return prev;
  }
  function withCtx(fn, ctx = currentRenderingInstance, isNonScopedSlot) {
    if (!ctx)
      return fn;
    if (fn._n) {
      return fn;
    }
    const renderFnWithContext = (...args) => {
      if (renderFnWithContext._d) {
        setBlockTracking(-1);
      }
      const prevInstance = setCurrentRenderingInstance(ctx);
      let res;
      try {
        res = fn(...args);
      } finally {
        setCurrentRenderingInstance(prevInstance);
        if (renderFnWithContext._d) {
          setBlockTracking(1);
        }
      }
      if (true) {
        devtoolsComponentUpdated(ctx);
      }
      return res;
    };
    renderFnWithContext._n = true;
    renderFnWithContext._c = true;
    renderFnWithContext._d = true;
    return renderFnWithContext;
  }
  function validateDirectiveName(name) {
    if (isBuiltInDirective(name)) {
      warn$1("Do not use built-in directive ids as custom directive id: " + name);
    }
  }
  function withDirectives(vnode, directives) {
    if (currentRenderingInstance === null) {
      warn$1(`withDirectives can only be used inside render functions.`);
      return vnode;
    }
    const instance = getComponentPublicInstance(currentRenderingInstance);
    const bindings = vnode.dirs || (vnode.dirs = []);
    for (let i = 0; i < directives.length; i++) {
      let [dir, value, arg, modifiers = EMPTY_OBJ] = directives[i];
      if (dir) {
        if (isFunction(dir)) {
          dir = {
            mounted: dir,
            updated: dir
          };
        }
        if (dir.deep) {
          traverse(value);
        }
        bindings.push({
          dir,
          instance,
          value,
          oldValue: void 0,
          arg,
          modifiers
        });
      }
    }
    return vnode;
  }
  function invokeDirectiveHook(vnode, prevVNode, instance, name) {
    const bindings = vnode.dirs;
    const oldBindings = prevVNode && prevVNode.dirs;
    for (let i = 0; i < bindings.length; i++) {
      const binding = bindings[i];
      if (oldBindings) {
        binding.oldValue = oldBindings[i].value;
      }
      let hook = binding.dir[name];
      if (hook) {
        pauseTracking();
        callWithAsyncErrorHandling(hook, instance, 8, [
          vnode.el,
          binding,
          vnode,
          prevVNode
        ]);
        resetTracking();
      }
    }
  }
  var TeleportEndKey = Symbol("_vte");
  var isTeleport = (type) => type.__isTeleport;
  var leaveCbKey = Symbol("_leaveCb");
  var enterCbKey = Symbol("_enterCb");
  function setTransitionHooks(vnode, hooks) {
    if (vnode.shapeFlag & 6 && vnode.component) {
      vnode.transition = hooks;
      setTransitionHooks(vnode.component.subTree, hooks);
    } else if (vnode.shapeFlag & 128) {
      vnode.ssContent.transition = hooks.clone(vnode.ssContent);
      vnode.ssFallback.transition = hooks.clone(vnode.ssFallback);
    } else {
      vnode.transition = hooks;
    }
  }
  // @__NO_SIDE_EFFECTS__
  function defineComponent(options, extraOptions) {
    return isFunction(options) ? (
      // #8236: extend call and options.name access are considered side-effects
      // by Rollup, so we have to wrap it in a pure-annotated IIFE.
      /* @__PURE__ */ (() => extend({ name: options.name }, extraOptions, { setup: options }))()
    ) : options;
  }
  function markAsyncBoundary(instance) {
    instance.ids = [instance.ids[0] + instance.ids[2]++ + "-", 0, 0];
  }
  var knownTemplateRefs = /* @__PURE__ */ new WeakSet();
  function setRef(rawRef, oldRawRef, parentSuspense, vnode, isUnmount = false) {
    if (isArray(rawRef)) {
      rawRef.forEach(
        (r, i) => setRef(
          r,
          oldRawRef && (isArray(oldRawRef) ? oldRawRef[i] : oldRawRef),
          parentSuspense,
          vnode,
          isUnmount
        )
      );
      return;
    }
    if (isAsyncWrapper(vnode) && !isUnmount) {
      if (vnode.shapeFlag & 512 && vnode.type.__asyncResolved && vnode.component.subTree.component) {
        setRef(rawRef, oldRawRef, parentSuspense, vnode.component.subTree);
      }
      return;
    }
    const refValue = vnode.shapeFlag & 4 ? getComponentPublicInstance(vnode.component) : vnode.el;
    const value = isUnmount ? null : refValue;
    const { i: owner, r: ref2 } = rawRef;
    if (!owner) {
      warn$1(
        `Missing ref owner context. ref cannot be used on hoisted vnodes. A vnode with ref must be created inside the render function.`
      );
      return;
    }
    const oldRef = oldRawRef && oldRawRef.r;
    const refs = owner.refs === EMPTY_OBJ ? owner.refs = {} : owner.refs;
    const setupState = owner.setupState;
    const rawSetupState = toRaw(setupState);
    const canSetSetupRef = setupState === EMPTY_OBJ ? () => false : (key) => {
      if (true) {
        if (hasOwn(rawSetupState, key) && !isRef2(rawSetupState[key])) {
          warn$1(
            `Template ref "${key}" used on a non-ref value. It will not work in the production build.`
          );
        }
        if (knownTemplateRefs.has(rawSetupState[key])) {
          return false;
        }
      }
      return hasOwn(rawSetupState, key);
    };
    if (oldRef != null && oldRef !== ref2) {
      if (isString(oldRef)) {
        refs[oldRef] = null;
        if (canSetSetupRef(oldRef)) {
          setupState[oldRef] = null;
        }
      } else if (isRef2(oldRef)) {
        oldRef.value = null;
      }
    }
    if (isFunction(ref2)) {
      callWithErrorHandling(ref2, owner, 12, [value, refs]);
    } else {
      const _isString = isString(ref2);
      const _isRef = isRef2(ref2);
      if (_isString || _isRef) {
        const doSet = () => {
          if (rawRef.f) {
            const existing = _isString ? canSetSetupRef(ref2) ? setupState[ref2] : refs[ref2] : ref2.value;
            if (isUnmount) {
              isArray(existing) && remove(existing, refValue);
            } else {
              if (!isArray(existing)) {
                if (_isString) {
                  refs[ref2] = [refValue];
                  if (canSetSetupRef(ref2)) {
                    setupState[ref2] = refs[ref2];
                  }
                } else {
                  ref2.value = [refValue];
                  if (rawRef.k)
                    refs[rawRef.k] = ref2.value;
                }
              } else if (!existing.includes(refValue)) {
                existing.push(refValue);
              }
            }
          } else if (_isString) {
            refs[ref2] = value;
            if (canSetSetupRef(ref2)) {
              setupState[ref2] = value;
            }
          } else if (_isRef) {
            ref2.value = value;
            if (rawRef.k)
              refs[rawRef.k] = value;
          } else if (true) {
            warn$1("Invalid template ref type:", ref2, `(${typeof ref2})`);
          }
        };
        if (value) {
          doSet.id = -1;
          queuePostRenderEffect(doSet, parentSuspense);
        } else {
          doSet();
        }
      } else if (true) {
        warn$1("Invalid template ref type:", ref2, `(${typeof ref2})`);
      }
    }
  }
  var requestIdleCallback = getGlobalThis().requestIdleCallback || ((cb) => setTimeout(cb, 1));
  var cancelIdleCallback = getGlobalThis().cancelIdleCallback || ((id) => clearTimeout(id));
  var isAsyncWrapper = (i) => !!i.type.__asyncLoader;
  var isKeepAlive = (vnode) => vnode.type.__isKeepAlive;
  function onActivated(hook, target) {
    registerKeepAliveHook(hook, "a", target);
  }
  function onDeactivated(hook, target) {
    registerKeepAliveHook(hook, "da", target);
  }
  function registerKeepAliveHook(hook, type, target = currentInstance) {
    const wrappedHook = hook.__wdc || (hook.__wdc = () => {
      let current = target;
      while (current) {
        if (current.isDeactivated) {
          return;
        }
        current = current.parent;
      }
      return hook();
    });
    injectHook(type, wrappedHook, target);
    if (target) {
      let current = target.parent;
      while (current && current.parent) {
        if (isKeepAlive(current.parent.vnode)) {
          injectToKeepAliveRoot(wrappedHook, type, target, current);
        }
        current = current.parent;
      }
    }
  }
  function injectToKeepAliveRoot(hook, type, target, keepAliveRoot) {
    const injected = injectHook(
      type,
      hook,
      keepAliveRoot,
      true
      /* prepend */
    );
    onUnmounted(() => {
      remove(keepAliveRoot[type], injected);
    }, target);
  }
  function injectHook(type, hook, target = currentInstance, prepend = false) {
    if (target) {
      const hooks = target[type] || (target[type] = []);
      const wrappedHook = hook.__weh || (hook.__weh = (...args) => {
        pauseTracking();
        const reset = setCurrentInstance(target);
        const res = callWithAsyncErrorHandling(hook, target, type, args);
        reset();
        resetTracking();
        return res;
      });
      if (prepend) {
        hooks.unshift(wrappedHook);
      } else {
        hooks.push(wrappedHook);
      }
      return wrappedHook;
    } else if (true) {
      const apiName = toHandlerKey(ErrorTypeStrings$1[type].replace(/ hook$/, ""));
      warn$1(
        `${apiName} is called when there is no active component instance to be associated with. Lifecycle injection APIs can only be used during execution of setup(). If you are using async setup(), make sure to register lifecycle hooks before the first await statement.`
      );
    }
  }
  var createHook = (lifecycle) => (hook, target = currentInstance) => {
    if (!isInSSRComponentSetup || lifecycle === "sp") {
      injectHook(lifecycle, (...args) => hook(...args), target);
    }
  };
  var onBeforeMount = createHook("bm");
  var onMounted = createHook("m");
  var onBeforeUpdate = createHook(
    "bu"
  );
  var onUpdated = createHook("u");
  var onBeforeUnmount = createHook(
    "bum"
  );
  var onUnmounted = createHook("um");
  var onServerPrefetch = createHook(
    "sp"
  );
  var onRenderTriggered = createHook("rtg");
  var onRenderTracked = createHook("rtc");
  function onErrorCaptured(hook, target = currentInstance) {
    injectHook("ec", hook, target);
  }
  var COMPONENTS = "components";
  var NULL_DYNAMIC_COMPONENT = Symbol.for("v-ndc");
  function resolveDynamicComponent(component) {
    if (isString(component)) {
      return resolveAsset(COMPONENTS, component, false) || component;
    } else {
      return component || NULL_DYNAMIC_COMPONENT;
    }
  }
  function resolveAsset(type, name, warnMissing = true, maybeSelfReference = false) {
    const instance = currentRenderingInstance || currentInstance;
    if (instance) {
      const Component = instance.type;
      if (type === COMPONENTS) {
        const selfName = getComponentName(
          Component,
          false
        );
        if (selfName && (selfName === name || selfName === camelize(name) || selfName === capitalize(camelize(name)))) {
          return Component;
        }
      }
      const res = (
        // local registration
        // check instance[type] first which is resolved for options API
        resolve(instance[type] || Component[type], name) || // global registration
        resolve(instance.appContext[type], name)
      );
      if (!res && maybeSelfReference) {
        return Component;
      }
      if (warnMissing && !res) {
        const extra = type === COMPONENTS ? `
If this is a native custom element, make sure to exclude it from component resolution via compilerOptions.isCustomElement.` : ``;
        warn$1(`Failed to resolve ${type.slice(0, -1)}: ${name}${extra}`);
      }
      return res;
    } else if (true) {
      warn$1(
        `resolve${capitalize(type.slice(0, -1))} can only be used in render() or setup().`
      );
    }
  }
  function resolve(registry, name) {
    return registry && (registry[name] || registry[camelize(name)] || registry[capitalize(camelize(name))]);
  }
  function renderList(source, renderItem, cache, index) {
    let ret;
    const cached = cache && cache[index];
    const sourceIsArray = isArray(source);
    if (sourceIsArray || isString(source)) {
      const sourceIsReactiveArray = sourceIsArray && isReactive(source);
      let needsWrap = false;
      if (sourceIsReactiveArray) {
        needsWrap = !isShallow(source);
        source = shallowReadArray(source);
      }
      ret = new Array(source.length);
      for (let i = 0, l = source.length; i < l; i++) {
        ret[i] = renderItem(
          needsWrap ? toReactive(source[i]) : source[i],
          i,
          void 0,
          cached && cached[i]
        );
      }
    } else if (typeof source === "number") {
      if (!Number.isInteger(source)) {
        warn$1(`The v-for range expect an integer value but got ${source}.`);
      }
      ret = new Array(source);
      for (let i = 0; i < source; i++) {
        ret[i] = renderItem(i + 1, i, void 0, cached && cached[i]);
      }
    } else if (isObject(source)) {
      if (source[Symbol.iterator]) {
        ret = Array.from(
          source,
          (item, i) => renderItem(item, i, void 0, cached && cached[i])
        );
      } else {
        const keys = Object.keys(source);
        ret = new Array(keys.length);
        for (let i = 0, l = keys.length; i < l; i++) {
          const key = keys[i];
          ret[i] = renderItem(source[key], key, i, cached && cached[i]);
        }
      }
    } else {
      ret = [];
    }
    if (cache) {
      cache[index] = ret;
    }
    return ret;
  }
  function renderSlot(slots, name, props = {}, fallback, noSlotted) {
    if (currentRenderingInstance.ce || currentRenderingInstance.parent && isAsyncWrapper(currentRenderingInstance.parent) && currentRenderingInstance.parent.ce) {
      if (name !== "default")
        props.name = name;
      return openBlock(), createBlock(
        Fragment,
        null,
        [createVNode("slot", props, fallback && fallback())],
        64
      );
    }
    let slot = slots[name];
    if (slot && slot.length > 1) {
      warn$1(
        `SSR-optimized slot function detected in a non-SSR-optimized render function. You need to mark this component with $dynamic-slots in the parent template.`
      );
      slot = () => [];
    }
    if (slot && slot._c) {
      slot._d = false;
    }
    openBlock();
    const validSlotContent = slot && ensureValidVNode(slot(props));
    const slotKey = props.key || // slot content array of a dynamic conditional slot may have a branch
    // key attached in the `createSlots` helper, respect that
    validSlotContent && validSlotContent.key;
    const rendered = createBlock(
      Fragment,
      {
        key: (slotKey && !isSymbol(slotKey) ? slotKey : `_${name}`) + // #7256 force differentiate fallback content from actual content
        (!validSlotContent && fallback ? "_fb" : "")
      },
      validSlotContent || (fallback ? fallback() : []),
      validSlotContent && slots._ === 1 ? 64 : -2
    );
    if (!noSlotted && rendered.scopeId) {
      rendered.slotScopeIds = [rendered.scopeId + "-s"];
    }
    if (slot && slot._c) {
      slot._d = true;
    }
    return rendered;
  }
  function ensureValidVNode(vnodes) {
    return vnodes.some((child) => {
      if (!isVNode(child))
        return true;
      if (child.type === Comment)
        return false;
      if (child.type === Fragment && !ensureValidVNode(child.children))
        return false;
      return true;
    }) ? vnodes : null;
  }
  var getPublicInstance = (i) => {
    if (!i)
      return null;
    if (isStatefulComponent(i))
      return getComponentPublicInstance(i);
    return getPublicInstance(i.parent);
  };
  var publicPropertiesMap = (
    // Move PURE marker to new line to workaround compiler discarding it
    // due to type annotation
    /* @__PURE__ */ extend(/* @__PURE__ */ Object.create(null), {
      $: (i) => i,
      $el: (i) => i.vnode.el,
      $data: (i) => i.data,
      $props: (i) => true ? shallowReadonly(i.props) : i.props,
      $attrs: (i) => true ? shallowReadonly(i.attrs) : i.attrs,
      $slots: (i) => true ? shallowReadonly(i.slots) : i.slots,
      $refs: (i) => true ? shallowReadonly(i.refs) : i.refs,
      $parent: (i) => getPublicInstance(i.parent),
      $root: (i) => getPublicInstance(i.root),
      $host: (i) => i.ce,
      $emit: (i) => i.emit,
      $options: (i) => true ? resolveMergedOptions(i) : i.type,
      $forceUpdate: (i) => i.f || (i.f = () => {
        queueJob(i.update);
      }),
      $nextTick: (i) => i.n || (i.n = nextTick.bind(i.proxy)),
      $watch: (i) => true ? instanceWatch.bind(i) : NOOP
    })
  );
  var isReservedPrefix = (key) => key === "_" || key === "$";
  var hasSetupBinding = (state, key) => state !== EMPTY_OBJ && !state.__isScriptSetup && hasOwn(state, key);
  var PublicInstanceProxyHandlers = {
    get({ _: instance }, key) {
      if (key === "__v_skip") {
        return true;
      }
      const { ctx, setupState, data, props, accessCache, type, appContext } = instance;
      if (key === "__isVue") {
        return true;
      }
      let normalizedProps;
      if (key[0] !== "$") {
        const n = accessCache[key];
        if (n !== void 0) {
          switch (n) {
            case 1:
              return setupState[key];
            case 2:
              return data[key];
            case 4:
              return ctx[key];
            case 3:
              return props[key];
          }
        } else if (hasSetupBinding(setupState, key)) {
          accessCache[key] = 1;
          return setupState[key];
        } else if (data !== EMPTY_OBJ && hasOwn(data, key)) {
          accessCache[key] = 2;
          return data[key];
        } else if (
          // only cache other properties when instance has declared (thus stable)
          // props
          (normalizedProps = instance.propsOptions[0]) && hasOwn(normalizedProps, key)
        ) {
          accessCache[key] = 3;
          return props[key];
        } else if (ctx !== EMPTY_OBJ && hasOwn(ctx, key)) {
          accessCache[key] = 4;
          return ctx[key];
        } else if (shouldCacheAccess) {
          accessCache[key] = 0;
        }
      }
      const publicGetter = publicPropertiesMap[key];
      let cssModule, globalProperties;
      if (publicGetter) {
        if (key === "$attrs") {
          track(instance.attrs, "get", "");
          markAttrsAccessed();
        } else if (key === "$slots") {
          track(instance, "get", key);
        }
        return publicGetter(instance);
      } else if (
        // css module (injected by vue-loader)
        (cssModule = type.__cssModules) && (cssModule = cssModule[key])
      ) {
        return cssModule;
      } else if (ctx !== EMPTY_OBJ && hasOwn(ctx, key)) {
        accessCache[key] = 4;
        return ctx[key];
      } else if (
        // global properties
        globalProperties = appContext.config.globalProperties, hasOwn(globalProperties, key)
      ) {
        {
          return globalProperties[key];
        }
      } else if (currentRenderingInstance && (!isString(key) || // #1091 avoid internal isRef/isVNode checks on component instance leading
      // to infinite warning loop
      key.indexOf("__v") !== 0)) {
        if (data !== EMPTY_OBJ && isReservedPrefix(key[0]) && hasOwn(data, key)) {
          warn$1(
            `Property ${JSON.stringify(
              key
            )} must be accessed via $data because it starts with a reserved character ("$" or "_") and is not proxied on the render context.`
          );
        } else if (instance === currentRenderingInstance) {
          warn$1(
            `Property ${JSON.stringify(key)} was accessed during render but is not defined on instance.`
          );
        }
      }
    },
    set({ _: instance }, key, value) {
      const { data, setupState, ctx } = instance;
      if (hasSetupBinding(setupState, key)) {
        setupState[key] = value;
        return true;
      } else if (setupState.__isScriptSetup && hasOwn(setupState, key)) {
        warn$1(`Cannot mutate <script setup> binding "${key}" from Options API.`);
        return false;
      } else if (data !== EMPTY_OBJ && hasOwn(data, key)) {
        data[key] = value;
        return true;
      } else if (hasOwn(instance.props, key)) {
        warn$1(`Attempting to mutate prop "${key}". Props are readonly.`);
        return false;
      }
      if (key[0] === "$" && key.slice(1) in instance) {
        warn$1(
          `Attempting to mutate public property "${key}". Properties starting with $ are reserved and readonly.`
        );
        return false;
      } else {
        if (key in instance.appContext.config.globalProperties) {
          Object.defineProperty(ctx, key, {
            enumerable: true,
            configurable: true,
            value
          });
        } else {
          ctx[key] = value;
        }
      }
      return true;
    },
    has({
      _: { data, setupState, accessCache, ctx, appContext, propsOptions }
    }, key) {
      let normalizedProps;
      return !!accessCache[key] || data !== EMPTY_OBJ && hasOwn(data, key) || hasSetupBinding(setupState, key) || (normalizedProps = propsOptions[0]) && hasOwn(normalizedProps, key) || hasOwn(ctx, key) || hasOwn(publicPropertiesMap, key) || hasOwn(appContext.config.globalProperties, key);
    },
    defineProperty(target, key, descriptor) {
      if (descriptor.get != null) {
        target._.accessCache[key] = 0;
      } else if (hasOwn(descriptor, "value")) {
        this.set(target, key, descriptor.value, null);
      }
      return Reflect.defineProperty(target, key, descriptor);
    }
  };
  if (true) {
    PublicInstanceProxyHandlers.ownKeys = (target) => {
      warn$1(
        `Avoid app logic that relies on enumerating keys on a component instance. The keys will be empty in production mode to avoid performance overhead.`
      );
      return Reflect.ownKeys(target);
    };
  }
  function createDevRenderContext(instance) {
    const target = {};
    Object.defineProperty(target, `_`, {
      configurable: true,
      enumerable: false,
      get: () => instance
    });
    Object.keys(publicPropertiesMap).forEach((key) => {
      Object.defineProperty(target, key, {
        configurable: true,
        enumerable: false,
        get: () => publicPropertiesMap[key](instance),
        // intercepted by the proxy so no need for implementation,
        // but needed to prevent set errors
        set: NOOP
      });
    });
    return target;
  }
  function exposePropsOnRenderContext(instance) {
    const {
      ctx,
      propsOptions: [propsOptions]
    } = instance;
    if (propsOptions) {
      Object.keys(propsOptions).forEach((key) => {
        Object.defineProperty(ctx, key, {
          enumerable: true,
          configurable: true,
          get: () => instance.props[key],
          set: NOOP
        });
      });
    }
  }
  function exposeSetupStateOnRenderContext(instance) {
    const { ctx, setupState } = instance;
    Object.keys(toRaw(setupState)).forEach((key) => {
      if (!setupState.__isScriptSetup) {
        if (isReservedPrefix(key[0])) {
          warn$1(
            `setup() return property ${JSON.stringify(
              key
            )} should not start with "$" or "_" which are reserved prefixes for Vue internals.`
          );
          return;
        }
        Object.defineProperty(ctx, key, {
          enumerable: true,
          configurable: true,
          get: () => setupState[key],
          set: NOOP
        });
      }
    });
  }
  function normalizePropsOrEmits(props) {
    return isArray(props) ? props.reduce(
      (normalized, p2) => (normalized[p2] = null, normalized),
      {}
    ) : props;
  }
  function createDuplicateChecker() {
    const cache = /* @__PURE__ */ Object.create(null);
    return (type, key) => {
      if (cache[key]) {
        warn$1(`${type} property "${key}" is already defined in ${cache[key]}.`);
      } else {
        cache[key] = type;
      }
    };
  }
  var shouldCacheAccess = true;
  function applyOptions(instance) {
    const options = resolveMergedOptions(instance);
    const publicThis = instance.proxy;
    const ctx = instance.ctx;
    shouldCacheAccess = false;
    if (options.beforeCreate) {
      callHook(options.beforeCreate, instance, "bc");
    }
    const {
      // state
      data: dataOptions,
      computed: computedOptions,
      methods,
      watch: watchOptions,
      provide: provideOptions,
      inject: injectOptions,
      // lifecycle
      created,
      beforeMount,
      mounted,
      beforeUpdate,
      updated,
      activated,
      deactivated,
      beforeDestroy,
      beforeUnmount,
      destroyed,
      unmounted,
      render: render15,
      renderTracked,
      renderTriggered,
      errorCaptured,
      serverPrefetch,
      // public API
      expose,
      inheritAttrs,
      // assets
      components,
      directives,
      filters
    } = options;
    const checkDuplicateProperties = true ? createDuplicateChecker() : null;
    if (true) {
      const [propsOptions] = instance.propsOptions;
      if (propsOptions) {
        for (const key in propsOptions) {
          checkDuplicateProperties("Props", key);
        }
      }
    }
    if (injectOptions) {
      resolveInjections(injectOptions, ctx, checkDuplicateProperties);
    }
    if (methods) {
      for (const key in methods) {
        const methodHandler = methods[key];
        if (isFunction(methodHandler)) {
          if (true) {
            Object.defineProperty(ctx, key, {
              value: methodHandler.bind(publicThis),
              configurable: true,
              enumerable: true,
              writable: true
            });
          } else {
            ctx[key] = methodHandler.bind(publicThis);
          }
          if (true) {
            checkDuplicateProperties("Methods", key);
          }
        } else if (true) {
          warn$1(
            `Method "${key}" has type "${typeof methodHandler}" in the component definition. Did you reference the function correctly?`
          );
        }
      }
    }
    if (dataOptions) {
      if (!isFunction(dataOptions)) {
        warn$1(
          `The data option must be a function. Plain object usage is no longer supported.`
        );
      }
      const data = dataOptions.call(publicThis, publicThis);
      if (isPromise(data)) {
        warn$1(
          `data() returned a Promise - note data() cannot be async; If you intend to perform data fetching before component renders, use async setup() + <Suspense>.`
        );
      }
      if (!isObject(data)) {
        warn$1(`data() should return an object.`);
      } else {
        instance.data = reactive(data);
        if (true) {
          for (const key in data) {
            checkDuplicateProperties("Data", key);
            if (!isReservedPrefix(key[0])) {
              Object.defineProperty(ctx, key, {
                configurable: true,
                enumerable: true,
                get: () => data[key],
                set: NOOP
              });
            }
          }
        }
      }
    }
    shouldCacheAccess = true;
    if (computedOptions) {
      for (const key in computedOptions) {
        const opt = computedOptions[key];
        const get = isFunction(opt) ? opt.bind(publicThis, publicThis) : isFunction(opt.get) ? opt.get.bind(publicThis, publicThis) : NOOP;
        if (get === NOOP) {
          warn$1(`Computed property "${key}" has no getter.`);
        }
        const set = !isFunction(opt) && isFunction(opt.set) ? opt.set.bind(publicThis) : true ? () => {
          warn$1(
            `Write operation failed: computed property "${key}" is readonly.`
          );
        } : NOOP;
        const c = computed2({
          get,
          set
        });
        Object.defineProperty(ctx, key, {
          enumerable: true,
          configurable: true,
          get: () => c.value,
          set: (v) => c.value = v
        });
        if (true) {
          checkDuplicateProperties("Computed", key);
        }
      }
    }
    if (watchOptions) {
      for (const key in watchOptions) {
        createWatcher(watchOptions[key], ctx, publicThis, key);
      }
    }
    if (provideOptions) {
      const provides = isFunction(provideOptions) ? provideOptions.call(publicThis) : provideOptions;
      Reflect.ownKeys(provides).forEach((key) => {
        provide(key, provides[key]);
      });
    }
    if (created) {
      callHook(created, instance, "c");
    }
    function registerLifecycleHook(register, hook) {
      if (isArray(hook)) {
        hook.forEach((_hook) => register(_hook.bind(publicThis)));
      } else if (hook) {
        register(hook.bind(publicThis));
      }
    }
    registerLifecycleHook(onBeforeMount, beforeMount);
    registerLifecycleHook(onMounted, mounted);
    registerLifecycleHook(onBeforeUpdate, beforeUpdate);
    registerLifecycleHook(onUpdated, updated);
    registerLifecycleHook(onActivated, activated);
    registerLifecycleHook(onDeactivated, deactivated);
    registerLifecycleHook(onErrorCaptured, errorCaptured);
    registerLifecycleHook(onRenderTracked, renderTracked);
    registerLifecycleHook(onRenderTriggered, renderTriggered);
    registerLifecycleHook(onBeforeUnmount, beforeUnmount);
    registerLifecycleHook(onUnmounted, unmounted);
    registerLifecycleHook(onServerPrefetch, serverPrefetch);
    if (isArray(expose)) {
      if (expose.length) {
        const exposed = instance.exposed || (instance.exposed = {});
        expose.forEach((key) => {
          Object.defineProperty(exposed, key, {
            get: () => publicThis[key],
            set: (val) => publicThis[key] = val
          });
        });
      } else if (!instance.exposed) {
        instance.exposed = {};
      }
    }
    if (render15 && instance.render === NOOP) {
      instance.render = render15;
    }
    if (inheritAttrs != null) {
      instance.inheritAttrs = inheritAttrs;
    }
    if (components)
      instance.components = components;
    if (directives)
      instance.directives = directives;
    if (serverPrefetch) {
      markAsyncBoundary(instance);
    }
  }
  function resolveInjections(injectOptions, ctx, checkDuplicateProperties = NOOP) {
    if (isArray(injectOptions)) {
      injectOptions = normalizeInject(injectOptions);
    }
    for (const key in injectOptions) {
      const opt = injectOptions[key];
      let injected;
      if (isObject(opt)) {
        if ("default" in opt) {
          injected = inject(
            opt.from || key,
            opt.default,
            true
          );
        } else {
          injected = inject(opt.from || key);
        }
      } else {
        injected = inject(opt);
      }
      if (isRef2(injected)) {
        Object.defineProperty(ctx, key, {
          enumerable: true,
          configurable: true,
          get: () => injected.value,
          set: (v) => injected.value = v
        });
      } else {
        ctx[key] = injected;
      }
      if (true) {
        checkDuplicateProperties("Inject", key);
      }
    }
  }
  function callHook(hook, instance, type) {
    callWithAsyncErrorHandling(
      isArray(hook) ? hook.map((h2) => h2.bind(instance.proxy)) : hook.bind(instance.proxy),
      instance,
      type
    );
  }
  function createWatcher(raw, ctx, publicThis, key) {
    let getter = key.includes(".") ? createPathGetter(publicThis, key) : () => publicThis[key];
    if (isString(raw)) {
      const handler = ctx[raw];
      if (isFunction(handler)) {
        {
          watch2(getter, handler);
        }
      } else if (true) {
        warn$1(`Invalid watch handler specified by key "${raw}"`, handler);
      }
    } else if (isFunction(raw)) {
      {
        watch2(getter, raw.bind(publicThis));
      }
    } else if (isObject(raw)) {
      if (isArray(raw)) {
        raw.forEach((r) => createWatcher(r, ctx, publicThis, key));
      } else {
        const handler = isFunction(raw.handler) ? raw.handler.bind(publicThis) : ctx[raw.handler];
        if (isFunction(handler)) {
          watch2(getter, handler, raw);
        } else if (true) {
          warn$1(`Invalid watch handler specified by key "${raw.handler}"`, handler);
        }
      }
    } else if (true) {
      warn$1(`Invalid watch option: "${key}"`, raw);
    }
  }
  function resolveMergedOptions(instance) {
    const base = instance.type;
    const { mixins, extends: extendsOptions } = base;
    const {
      mixins: globalMixins,
      optionsCache: cache,
      config: { optionMergeStrategies }
    } = instance.appContext;
    const cached = cache.get(base);
    let resolved;
    if (cached) {
      resolved = cached;
    } else if (!globalMixins.length && !mixins && !extendsOptions) {
      {
        resolved = base;
      }
    } else {
      resolved = {};
      if (globalMixins.length) {
        globalMixins.forEach(
          (m) => mergeOptions(resolved, m, optionMergeStrategies, true)
        );
      }
      mergeOptions(resolved, base, optionMergeStrategies);
    }
    if (isObject(base)) {
      cache.set(base, resolved);
    }
    return resolved;
  }
  function mergeOptions(to, from, strats, asMixin = false) {
    const { mixins, extends: extendsOptions } = from;
    if (extendsOptions) {
      mergeOptions(to, extendsOptions, strats, true);
    }
    if (mixins) {
      mixins.forEach(
        (m) => mergeOptions(to, m, strats, true)
      );
    }
    for (const key in from) {
      if (asMixin && key === "expose") {
        warn$1(
          `"expose" option is ignored when declared in mixins or extends. It should only be declared in the base component itself.`
        );
      } else {
        const strat = internalOptionMergeStrats[key] || strats && strats[key];
        to[key] = strat ? strat(to[key], from[key]) : from[key];
      }
    }
    return to;
  }
  var internalOptionMergeStrats = {
    data: mergeDataFn,
    props: mergeEmitsOrPropsOptions,
    emits: mergeEmitsOrPropsOptions,
    // objects
    methods: mergeObjectOptions,
    computed: mergeObjectOptions,
    // lifecycle
    beforeCreate: mergeAsArray,
    created: mergeAsArray,
    beforeMount: mergeAsArray,
    mounted: mergeAsArray,
    beforeUpdate: mergeAsArray,
    updated: mergeAsArray,
    beforeDestroy: mergeAsArray,
    beforeUnmount: mergeAsArray,
    destroyed: mergeAsArray,
    unmounted: mergeAsArray,
    activated: mergeAsArray,
    deactivated: mergeAsArray,
    errorCaptured: mergeAsArray,
    serverPrefetch: mergeAsArray,
    // assets
    components: mergeObjectOptions,
    directives: mergeObjectOptions,
    // watch
    watch: mergeWatchOptions,
    // provide / inject
    provide: mergeDataFn,
    inject: mergeInject
  };
  function mergeDataFn(to, from) {
    if (!from) {
      return to;
    }
    if (!to) {
      return from;
    }
    return function mergedDataFn() {
      return extend(
        isFunction(to) ? to.call(this, this) : to,
        isFunction(from) ? from.call(this, this) : from
      );
    };
  }
  function mergeInject(to, from) {
    return mergeObjectOptions(normalizeInject(to), normalizeInject(from));
  }
  function normalizeInject(raw) {
    if (isArray(raw)) {
      const res = {};
      for (let i = 0; i < raw.length; i++) {
        res[raw[i]] = raw[i];
      }
      return res;
    }
    return raw;
  }
  function mergeAsArray(to, from) {
    return to ? [...new Set([].concat(to, from))] : from;
  }
  function mergeObjectOptions(to, from) {
    return to ? extend(/* @__PURE__ */ Object.create(null), to, from) : from;
  }
  function mergeEmitsOrPropsOptions(to, from) {
    if (to) {
      if (isArray(to) && isArray(from)) {
        return [.../* @__PURE__ */ new Set([...to, ...from])];
      }
      return extend(
        /* @__PURE__ */ Object.create(null),
        normalizePropsOrEmits(to),
        normalizePropsOrEmits(from != null ? from : {})
      );
    } else {
      return from;
    }
  }
  function mergeWatchOptions(to, from) {
    if (!to)
      return from;
    if (!from)
      return to;
    const merged = extend(/* @__PURE__ */ Object.create(null), to);
    for (const key in from) {
      merged[key] = mergeAsArray(to[key], from[key]);
    }
    return merged;
  }
  function createAppContext() {
    return {
      app: null,
      config: {
        isNativeTag: NO,
        performance: false,
        globalProperties: {},
        optionMergeStrategies: {},
        errorHandler: void 0,
        warnHandler: void 0,
        compilerOptions: {}
      },
      mixins: [],
      components: {},
      directives: {},
      provides: /* @__PURE__ */ Object.create(null),
      optionsCache: /* @__PURE__ */ new WeakMap(),
      propsCache: /* @__PURE__ */ new WeakMap(),
      emitsCache: /* @__PURE__ */ new WeakMap()
    };
  }
  var uid$1 = 0;
  function createAppAPI(render15, hydrate) {
    return function createApp2(rootComponent, rootProps = null) {
      if (!isFunction(rootComponent)) {
        rootComponent = extend({}, rootComponent);
      }
      if (rootProps != null && !isObject(rootProps)) {
        warn$1(`root props passed to app.mount() must be an object.`);
        rootProps = null;
      }
      const context = createAppContext();
      const installedPlugins = /* @__PURE__ */ new WeakSet();
      const pluginCleanupFns = [];
      let isMounted = false;
      const app2 = context.app = {
        _uid: uid$1++,
        _component: rootComponent,
        _props: rootProps,
        _container: null,
        _context: context,
        _instance: null,
        version,
        get config() {
          return context.config;
        },
        set config(v) {
          if (true) {
            warn$1(
              `app.config cannot be replaced. Modify individual options instead.`
            );
          }
        },
        use(plugin, ...options) {
          if (installedPlugins.has(plugin)) {
            warn$1(`Plugin has already been applied to target app.`);
          } else if (plugin && isFunction(plugin.install)) {
            installedPlugins.add(plugin);
            plugin.install(app2, ...options);
          } else if (isFunction(plugin)) {
            installedPlugins.add(plugin);
            plugin(app2, ...options);
          } else if (true) {
            warn$1(
              `A plugin must either be a function or an object with an "install" function.`
            );
          }
          return app2;
        },
        mixin(mixin) {
          if (true) {
            if (!context.mixins.includes(mixin)) {
              context.mixins.push(mixin);
            } else if (true) {
              warn$1(
                "Mixin has already been applied to target app" + (mixin.name ? `: ${mixin.name}` : "")
              );
            }
          } else if (true) {
            warn$1("Mixins are only available in builds supporting Options API");
          }
          return app2;
        },
        component(name, component) {
          if (true) {
            validateComponentName(name, context.config);
          }
          if (!component) {
            return context.components[name];
          }
          if (context.components[name]) {
            warn$1(`Component "${name}" has already been registered in target app.`);
          }
          context.components[name] = component;
          return app2;
        },
        directive(name, directive) {
          if (true) {
            validateDirectiveName(name);
          }
          if (!directive) {
            return context.directives[name];
          }
          if (context.directives[name]) {
            warn$1(`Directive "${name}" has already been registered in target app.`);
          }
          context.directives[name] = directive;
          return app2;
        },
        mount(rootContainer, isHydrate, namespace) {
          if (!isMounted) {
            if (rootContainer.__vue_app__) {
              warn$1(
                `There is already an app instance mounted on the host container.
 If you want to mount another app on the same host container, you need to unmount the previous app by calling \`app.unmount()\` first.`
              );
            }
            const vnode = app2._ceVNode || createVNode(rootComponent, rootProps);
            vnode.appContext = context;
            if (namespace === true) {
              namespace = "svg";
            } else if (namespace === false) {
              namespace = void 0;
            }
            if (true) {
              context.reload = () => {
                render15(
                  cloneVNode(vnode),
                  rootContainer,
                  namespace
                );
              };
            }
            if (isHydrate && hydrate) {
              hydrate(vnode, rootContainer);
            } else {
              render15(vnode, rootContainer, namespace);
            }
            isMounted = true;
            app2._container = rootContainer;
            rootContainer.__vue_app__ = app2;
            if (true) {
              app2._instance = vnode.component;
              devtoolsInitApp(app2, version);
            }
            return getComponentPublicInstance(vnode.component);
          } else if (true) {
            warn$1(
              `App has already been mounted.
If you want to remount the same app, move your app creation logic into a factory function and create fresh app instances for each mount - e.g. \`const createMyApp = () => createApp(App)\``
            );
          }
        },
        onUnmount(cleanupFn) {
          if (typeof cleanupFn !== "function") {
            warn$1(
              `Expected function as first argument to app.onUnmount(), but got ${typeof cleanupFn}`
            );
          }
          pluginCleanupFns.push(cleanupFn);
        },
        unmount() {
          if (isMounted) {
            callWithAsyncErrorHandling(
              pluginCleanupFns,
              app2._instance,
              16
            );
            render15(null, app2._container);
            if (true) {
              app2._instance = null;
              devtoolsUnmountApp(app2);
            }
            delete app2._container.__vue_app__;
          } else if (true) {
            warn$1(`Cannot unmount an app that is not mounted.`);
          }
        },
        provide(key, value) {
          if (key in context.provides) {
            warn$1(
              `App already provides property with key "${String(key)}". It will be overwritten with the new value.`
            );
          }
          context.provides[key] = value;
          return app2;
        },
        runWithContext(fn) {
          const lastApp = currentApp;
          currentApp = app2;
          try {
            return fn();
          } finally {
            currentApp = lastApp;
          }
        }
      };
      return app2;
    };
  }
  var currentApp = null;
  function provide(key, value) {
    if (!currentInstance) {
      if (true) {
        warn$1(`provide() can only be used inside setup().`);
      }
    } else {
      let provides = currentInstance.provides;
      const parentProvides = currentInstance.parent && currentInstance.parent.provides;
      if (parentProvides === provides) {
        provides = currentInstance.provides = Object.create(parentProvides);
      }
      provides[key] = value;
    }
  }
  function inject(key, defaultValue, treatDefaultAsFactory = false) {
    const instance = currentInstance || currentRenderingInstance;
    if (instance || currentApp) {
      const provides = currentApp ? currentApp._context.provides : instance ? instance.parent == null ? instance.vnode.appContext && instance.vnode.appContext.provides : instance.parent.provides : void 0;
      if (provides && key in provides) {
        return provides[key];
      } else if (arguments.length > 1) {
        return treatDefaultAsFactory && isFunction(defaultValue) ? defaultValue.call(instance && instance.proxy) : defaultValue;
      } else if (true) {
        warn$1(`injection "${String(key)}" not found.`);
      }
    } else if (true) {
      warn$1(`inject() can only be used inside setup() or functional components.`);
    }
  }
  var internalObjectProto = {};
  var createInternalObject = () => Object.create(internalObjectProto);
  var isInternalObject = (obj) => Object.getPrototypeOf(obj) === internalObjectProto;
  function initProps(instance, rawProps, isStateful, isSSR = false) {
    const props = {};
    const attrs = createInternalObject();
    instance.propsDefaults = /* @__PURE__ */ Object.create(null);
    setFullProps(instance, rawProps, props, attrs);
    for (const key in instance.propsOptions[0]) {
      if (!(key in props)) {
        props[key] = void 0;
      }
    }
    if (true) {
      validateProps(rawProps || {}, props, instance);
    }
    if (isStateful) {
      instance.props = isSSR ? props : shallowReactive(props);
    } else {
      if (!instance.type.props) {
        instance.props = attrs;
      } else {
        instance.props = props;
      }
    }
    instance.attrs = attrs;
  }
  function isInHmrContext(instance) {
    while (instance) {
      if (instance.type.__hmrId)
        return true;
      instance = instance.parent;
    }
  }
  function updateProps(instance, rawProps, rawPrevProps, optimized) {
    const {
      props,
      attrs,
      vnode: { patchFlag }
    } = instance;
    const rawCurrentProps = toRaw(props);
    const [options] = instance.propsOptions;
    let hasAttrsChanged = false;
    if (
      // always force full diff in dev
      // - #1942 if hmr is enabled with sfc component
      // - vite#872 non-sfc component used by sfc component
      !isInHmrContext(instance) && (optimized || patchFlag > 0) && !(patchFlag & 16)
    ) {
      if (patchFlag & 8) {
        const propsToUpdate = instance.vnode.dynamicProps;
        for (let i = 0; i < propsToUpdate.length; i++) {
          let key = propsToUpdate[i];
          if (isEmitListener(instance.emitsOptions, key)) {
            continue;
          }
          const value = rawProps[key];
          if (options) {
            if (hasOwn(attrs, key)) {
              if (value !== attrs[key]) {
                attrs[key] = value;
                hasAttrsChanged = true;
              }
            } else {
              const camelizedKey = camelize(key);
              props[camelizedKey] = resolvePropValue(
                options,
                rawCurrentProps,
                camelizedKey,
                value,
                instance,
                false
              );
            }
          } else {
            if (value !== attrs[key]) {
              attrs[key] = value;
              hasAttrsChanged = true;
            }
          }
        }
      }
    } else {
      if (setFullProps(instance, rawProps, props, attrs)) {
        hasAttrsChanged = true;
      }
      let kebabKey;
      for (const key in rawCurrentProps) {
        if (!rawProps || // for camelCase
        !hasOwn(rawProps, key) && // it's possible the original props was passed in as kebab-case
        // and converted to camelCase (#955)
        ((kebabKey = hyphenate(key)) === key || !hasOwn(rawProps, kebabKey))) {
          if (options) {
            if (rawPrevProps && // for camelCase
            (rawPrevProps[key] !== void 0 || // for kebab-case
            rawPrevProps[kebabKey] !== void 0)) {
              props[key] = resolvePropValue(
                options,
                rawCurrentProps,
                key,
                void 0,
                instance,
                true
              );
            }
          } else {
            delete props[key];
          }
        }
      }
      if (attrs !== rawCurrentProps) {
        for (const key in attrs) {
          if (!rawProps || !hasOwn(rawProps, key) && true) {
            delete attrs[key];
            hasAttrsChanged = true;
          }
        }
      }
    }
    if (hasAttrsChanged) {
      trigger(instance.attrs, "set", "");
    }
    if (true) {
      validateProps(rawProps || {}, props, instance);
    }
  }
  function setFullProps(instance, rawProps, props, attrs) {
    const [options, needCastKeys] = instance.propsOptions;
    let hasAttrsChanged = false;
    let rawCastValues;
    if (rawProps) {
      for (let key in rawProps) {
        if (isReservedProp(key)) {
          continue;
        }
        const value = rawProps[key];
        let camelKey;
        if (options && hasOwn(options, camelKey = camelize(key))) {
          if (!needCastKeys || !needCastKeys.includes(camelKey)) {
            props[camelKey] = value;
          } else {
            (rawCastValues || (rawCastValues = {}))[camelKey] = value;
          }
        } else if (!isEmitListener(instance.emitsOptions, key)) {
          if (!(key in attrs) || value !== attrs[key]) {
            attrs[key] = value;
            hasAttrsChanged = true;
          }
        }
      }
    }
    if (needCastKeys) {
      const rawCurrentProps = toRaw(props);
      const castValues = rawCastValues || EMPTY_OBJ;
      for (let i = 0; i < needCastKeys.length; i++) {
        const key = needCastKeys[i];
        props[key] = resolvePropValue(
          options,
          rawCurrentProps,
          key,
          castValues[key],
          instance,
          !hasOwn(castValues, key)
        );
      }
    }
    return hasAttrsChanged;
  }
  function resolvePropValue(options, props, key, value, instance, isAbsent) {
    const opt = options[key];
    if (opt != null) {
      const hasDefault = hasOwn(opt, "default");
      if (hasDefault && value === void 0) {
        const defaultValue = opt.default;
        if (opt.type !== Function && !opt.skipFactory && isFunction(defaultValue)) {
          const { propsDefaults } = instance;
          if (key in propsDefaults) {
            value = propsDefaults[key];
          } else {
            const reset = setCurrentInstance(instance);
            value = propsDefaults[key] = defaultValue.call(
              null,
              props
            );
            reset();
          }
        } else {
          value = defaultValue;
        }
        if (instance.ce) {
          instance.ce._setProp(key, value);
        }
      }
      if (opt[
        0
        /* shouldCast */
      ]) {
        if (isAbsent && !hasDefault) {
          value = false;
        } else if (opt[
          1
          /* shouldCastTrue */
        ] && (value === "" || value === hyphenate(key))) {
          value = true;
        }
      }
    }
    return value;
  }
  var mixinPropsCache = /* @__PURE__ */ new WeakMap();
  function normalizePropsOptions(comp, appContext, asMixin = false) {
    const cache = asMixin ? mixinPropsCache : appContext.propsCache;
    const cached = cache.get(comp);
    if (cached) {
      return cached;
    }
    const raw = comp.props;
    const normalized = {};
    const needCastKeys = [];
    let hasExtends = false;
    if (!isFunction(comp)) {
      const extendProps = (raw2) => {
        hasExtends = true;
        const [props, keys] = normalizePropsOptions(raw2, appContext, true);
        extend(normalized, props);
        if (keys)
          needCastKeys.push(...keys);
      };
      if (!asMixin && appContext.mixins.length) {
        appContext.mixins.forEach(extendProps);
      }
      if (comp.extends) {
        extendProps(comp.extends);
      }
      if (comp.mixins) {
        comp.mixins.forEach(extendProps);
      }
    }
    if (!raw && !hasExtends) {
      if (isObject(comp)) {
        cache.set(comp, EMPTY_ARR);
      }
      return EMPTY_ARR;
    }
    if (isArray(raw)) {
      for (let i = 0; i < raw.length; i++) {
        if (!isString(raw[i])) {
          warn$1(`props must be strings when using array syntax.`, raw[i]);
        }
        const normalizedKey = camelize(raw[i]);
        if (validatePropName(normalizedKey)) {
          normalized[normalizedKey] = EMPTY_OBJ;
        }
      }
    } else if (raw) {
      if (!isObject(raw)) {
        warn$1(`invalid props options`, raw);
      }
      for (const key in raw) {
        const normalizedKey = camelize(key);
        if (validatePropName(normalizedKey)) {
          const opt = raw[key];
          const prop = normalized[normalizedKey] = isArray(opt) || isFunction(opt) ? { type: opt } : extend({}, opt);
          const propType = prop.type;
          let shouldCast = false;
          let shouldCastTrue = true;
          if (isArray(propType)) {
            for (let index = 0; index < propType.length; ++index) {
              const type = propType[index];
              const typeName = isFunction(type) && type.name;
              if (typeName === "Boolean") {
                shouldCast = true;
                break;
              } else if (typeName === "String") {
                shouldCastTrue = false;
              }
            }
          } else {
            shouldCast = isFunction(propType) && propType.name === "Boolean";
          }
          prop[
            0
            /* shouldCast */
          ] = shouldCast;
          prop[
            1
            /* shouldCastTrue */
          ] = shouldCastTrue;
          if (shouldCast || hasOwn(prop, "default")) {
            needCastKeys.push(normalizedKey);
          }
        }
      }
    }
    const res = [normalized, needCastKeys];
    if (isObject(comp)) {
      cache.set(comp, res);
    }
    return res;
  }
  function validatePropName(key) {
    if (key[0] !== "$" && !isReservedProp(key)) {
      return true;
    } else if (true) {
      warn$1(`Invalid prop name: "${key}" is a reserved property.`);
    }
    return false;
  }
  function getType(ctor) {
    if (ctor === null) {
      return "null";
    }
    if (typeof ctor === "function") {
      return ctor.name || "";
    } else if (typeof ctor === "object") {
      const name = ctor.constructor && ctor.constructor.name;
      return name || "";
    }
    return "";
  }
  function validateProps(rawProps, props, instance) {
    const resolvedValues = toRaw(props);
    const options = instance.propsOptions[0];
    const camelizePropsKey = Object.keys(rawProps).map((key) => camelize(key));
    for (const key in options) {
      let opt = options[key];
      if (opt == null)
        continue;
      validateProp(
        key,
        resolvedValues[key],
        opt,
        true ? shallowReadonly(resolvedValues) : resolvedValues,
        !camelizePropsKey.includes(key)
      );
    }
  }
  function validateProp(name, value, prop, props, isAbsent) {
    const { type, required, validator, skipCheck } = prop;
    if (required && isAbsent) {
      warn$1('Missing required prop: "' + name + '"');
      return;
    }
    if (value == null && !required) {
      return;
    }
    if (type != null && type !== true && !skipCheck) {
      let isValid = false;
      const types = isArray(type) ? type : [type];
      const expectedTypes = [];
      for (let i = 0; i < types.length && !isValid; i++) {
        const { valid, expectedType } = assertType(value, types[i]);
        expectedTypes.push(expectedType || "");
        isValid = valid;
      }
      if (!isValid) {
        warn$1(getInvalidTypeMessage(name, value, expectedTypes));
        return;
      }
    }
    if (validator && !validator(value, props)) {
      warn$1('Invalid prop: custom validator check failed for prop "' + name + '".');
    }
  }
  var isSimpleType = /* @__PURE__ */ makeMap(
    "String,Number,Boolean,Function,Symbol,BigInt"
  );
  function assertType(value, type) {
    let valid;
    const expectedType = getType(type);
    if (expectedType === "null") {
      valid = value === null;
    } else if (isSimpleType(expectedType)) {
      const t = typeof value;
      valid = t === expectedType.toLowerCase();
      if (!valid && t === "object") {
        valid = value instanceof type;
      }
    } else if (expectedType === "Object") {
      valid = isObject(value);
    } else if (expectedType === "Array") {
      valid = isArray(value);
    } else {
      valid = value instanceof type;
    }
    return {
      valid,
      expectedType
    };
  }
  function getInvalidTypeMessage(name, value, expectedTypes) {
    if (expectedTypes.length === 0) {
      return `Prop type [] for prop "${name}" won't match anything. Did you mean to use type Array instead?`;
    }
    let message = `Invalid prop: type check failed for prop "${name}". Expected ${expectedTypes.map(capitalize).join(" | ")}`;
    const expectedType = expectedTypes[0];
    const receivedType = toRawType(value);
    const expectedValue = styleValue(value, expectedType);
    const receivedValue = styleValue(value, receivedType);
    if (expectedTypes.length === 1 && isExplicable(expectedType) && !isBoolean(expectedType, receivedType)) {
      message += ` with value ${expectedValue}`;
    }
    message += `, got ${receivedType} `;
    if (isExplicable(receivedType)) {
      message += `with value ${receivedValue}.`;
    }
    return message;
  }
  function styleValue(value, type) {
    if (type === "String") {
      return `"${value}"`;
    } else if (type === "Number") {
      return `${Number(value)}`;
    } else {
      return `${value}`;
    }
  }
  function isExplicable(type) {
    const explicitTypes = ["string", "number", "boolean"];
    return explicitTypes.some((elem) => type.toLowerCase() === elem);
  }
  function isBoolean(...args) {
    return args.some((elem) => elem.toLowerCase() === "boolean");
  }
  var isInternalKey = (key) => key[0] === "_" || key === "$stable";
  var normalizeSlotValue = (value) => isArray(value) ? value.map(normalizeVNode) : [normalizeVNode(value)];
  var normalizeSlot = (key, rawSlot, ctx) => {
    if (rawSlot._n) {
      return rawSlot;
    }
    const normalized = withCtx((...args) => {
      if (currentInstance && (!ctx || ctx.root === currentInstance.root)) {
        warn$1(
          `Slot "${key}" invoked outside of the render function: this will not track dependencies used in the slot. Invoke the slot function inside the render function instead.`
        );
      }
      return normalizeSlotValue(rawSlot(...args));
    }, ctx);
    normalized._c = false;
    return normalized;
  };
  var normalizeObjectSlots = (rawSlots, slots, instance) => {
    const ctx = rawSlots._ctx;
    for (const key in rawSlots) {
      if (isInternalKey(key))
        continue;
      const value = rawSlots[key];
      if (isFunction(value)) {
        slots[key] = normalizeSlot(key, value, ctx);
      } else if (value != null) {
        if (true) {
          warn$1(
            `Non-function value encountered for slot "${key}". Prefer function slots for better performance.`
          );
        }
        const normalized = normalizeSlotValue(value);
        slots[key] = () => normalized;
      }
    }
  };
  var normalizeVNodeSlots = (instance, children) => {
    if (!isKeepAlive(instance.vnode) && true) {
      warn$1(
        `Non-function value encountered for default slot. Prefer function slots for better performance.`
      );
    }
    const normalized = normalizeSlotValue(children);
    instance.slots.default = () => normalized;
  };
  var assignSlots = (slots, children, optimized) => {
    for (const key in children) {
      if (optimized || key !== "_") {
        slots[key] = children[key];
      }
    }
  };
  var initSlots = (instance, children, optimized) => {
    const slots = instance.slots = createInternalObject();
    if (instance.vnode.shapeFlag & 32) {
      const type = children._;
      if (type) {
        assignSlots(slots, children, optimized);
        if (optimized) {
          def(slots, "_", type, true);
        }
      } else {
        normalizeObjectSlots(children, slots);
      }
    } else if (children) {
      normalizeVNodeSlots(instance, children);
    }
  };
  var updateSlots = (instance, children, optimized) => {
    const { vnode, slots } = instance;
    let needDeletionCheck = true;
    let deletionComparisonTarget = EMPTY_OBJ;
    if (vnode.shapeFlag & 32) {
      const type = children._;
      if (type) {
        if (isHmrUpdating) {
          assignSlots(slots, children, optimized);
          trigger(instance, "set", "$slots");
        } else if (optimized && type === 1) {
          needDeletionCheck = false;
        } else {
          assignSlots(slots, children, optimized);
        }
      } else {
        needDeletionCheck = !children.$stable;
        normalizeObjectSlots(children, slots);
      }
      deletionComparisonTarget = children;
    } else if (children) {
      normalizeVNodeSlots(instance, children);
      deletionComparisonTarget = { default: 1 };
    }
    if (needDeletionCheck) {
      for (const key in slots) {
        if (!isInternalKey(key) && deletionComparisonTarget[key] == null) {
          delete slots[key];
        }
      }
    }
  };
  var supported;
  var perf;
  function startMeasure(instance, type) {
    if (instance.appContext.config.performance && isSupported()) {
      perf.mark(`vue-${type}-${instance.uid}`);
    }
    if (true) {
      devtoolsPerfStart(instance, type, isSupported() ? perf.now() : Date.now());
    }
  }
  function endMeasure(instance, type) {
    if (instance.appContext.config.performance && isSupported()) {
      const startTag = `vue-${type}-${instance.uid}`;
      const endTag = startTag + `:end`;
      perf.mark(endTag);
      perf.measure(
        `<${formatComponentName(instance, instance.type)}> ${type}`,
        startTag,
        endTag
      );
      perf.clearMarks(startTag);
      perf.clearMarks(endTag);
    }
    if (true) {
      devtoolsPerfEnd(instance, type, isSupported() ? perf.now() : Date.now());
    }
  }
  function isSupported() {
    if (supported !== void 0) {
      return supported;
    }
    if (typeof window !== "undefined" && window.performance) {
      supported = true;
      perf = window.performance;
    } else {
      supported = false;
    }
    return supported;
  }
  function initFeatureFlags() {
    const needWarn = [];
    if (false) {
      needWarn.push(`__VUE_OPTIONS_API__`);
      getGlobalThis().__VUE_OPTIONS_API__ = true;
    }
    if (false) {
      needWarn.push(`__VUE_PROD_DEVTOOLS__`);
      getGlobalThis().__VUE_PROD_DEVTOOLS__ = false;
    }
    if (false) {
      needWarn.push(`__VUE_PROD_HYDRATION_MISMATCH_DETAILS__`);
      getGlobalThis().__VUE_PROD_HYDRATION_MISMATCH_DETAILS__ = false;
    }
    if (needWarn.length) {
      const multi = needWarn.length > 1;
      console.warn(
        `Feature flag${multi ? `s` : ``} ${needWarn.join(", ")} ${multi ? `are` : `is`} not explicitly defined. You are running the esm-bundler build of Vue, which expects these compile-time feature flags to be globally injected via the bundler config in order to get better tree-shaking in the production bundle.

For more details, see https://link.vuejs.org/feature-flags.`
      );
    }
  }
  var queuePostRenderEffect = queueEffectWithSuspense;
  function createRenderer(options) {
    return baseCreateRenderer(options);
  }
  function baseCreateRenderer(options, createHydrationFns) {
    {
      initFeatureFlags();
    }
    const target = getGlobalThis();
    target.__VUE__ = true;
    if (true) {
      setDevtoolsHook$1(target.__VUE_DEVTOOLS_GLOBAL_HOOK__, target);
    }
    const {
      insert: hostInsert,
      remove: hostRemove,
      patchProp: hostPatchProp,
      createElement: hostCreateElement,
      createText: hostCreateText,
      createComment: hostCreateComment,
      setText: hostSetText,
      setElementText: hostSetElementText,
      parentNode: hostParentNode,
      nextSibling: hostNextSibling,
      setScopeId: hostSetScopeId = NOOP,
      insertStaticContent: hostInsertStaticContent
    } = options;
    const patch = (n1, n2, container, anchor = null, parentComponent = null, parentSuspense = null, namespace = void 0, slotScopeIds = null, optimized = isHmrUpdating ? false : !!n2.dynamicChildren) => {
      if (n1 === n2) {
        return;
      }
      if (n1 && !isSameVNodeType(n1, n2)) {
        anchor = getNextHostNode(n1);
        unmount(n1, parentComponent, parentSuspense, true);
        n1 = null;
      }
      if (n2.patchFlag === -2) {
        optimized = false;
        n2.dynamicChildren = null;
      }
      const { type, ref: ref2, shapeFlag } = n2;
      switch (type) {
        case Text:
          processText(n1, n2, container, anchor);
          break;
        case Comment:
          processCommentNode(n1, n2, container, anchor);
          break;
        case Static:
          if (n1 == null) {
            mountStaticNode(n2, container, anchor, namespace);
          } else if (true) {
            patchStaticNode(n1, n2, container, namespace);
          }
          break;
        case Fragment:
          processFragment(
            n1,
            n2,
            container,
            anchor,
            parentComponent,
            parentSuspense,
            namespace,
            slotScopeIds,
            optimized
          );
          break;
        default:
          if (shapeFlag & 1) {
            processElement(
              n1,
              n2,
              container,
              anchor,
              parentComponent,
              parentSuspense,
              namespace,
              slotScopeIds,
              optimized
            );
          } else if (shapeFlag & 6) {
            processComponent(
              n1,
              n2,
              container,
              anchor,
              parentComponent,
              parentSuspense,
              namespace,
              slotScopeIds,
              optimized
            );
          } else if (shapeFlag & 64) {
            type.process(
              n1,
              n2,
              container,
              anchor,
              parentComponent,
              parentSuspense,
              namespace,
              slotScopeIds,
              optimized,
              internals
            );
          } else if (shapeFlag & 128) {
            type.process(
              n1,
              n2,
              container,
              anchor,
              parentComponent,
              parentSuspense,
              namespace,
              slotScopeIds,
              optimized,
              internals
            );
          } else if (true) {
            warn$1("Invalid VNode type:", type, `(${typeof type})`);
          }
      }
      if (ref2 != null && parentComponent) {
        setRef(ref2, n1 && n1.ref, parentSuspense, n2 || n1, !n2);
      }
    };
    const processText = (n1, n2, container, anchor) => {
      if (n1 == null) {
        hostInsert(
          n2.el = hostCreateText(n2.children),
          container,
          anchor
        );
      } else {
        const el = n2.el = n1.el;
        if (n2.children !== n1.children) {
          hostSetText(el, n2.children);
        }
      }
    };
    const processCommentNode = (n1, n2, container, anchor) => {
      if (n1 == null) {
        hostInsert(
          n2.el = hostCreateComment(n2.children || ""),
          container,
          anchor
        );
      } else {
        n2.el = n1.el;
      }
    };
    const mountStaticNode = (n2, container, anchor, namespace) => {
      [n2.el, n2.anchor] = hostInsertStaticContent(
        n2.children,
        container,
        anchor,
        namespace,
        n2.el,
        n2.anchor
      );
    };
    const patchStaticNode = (n1, n2, container, namespace) => {
      if (n2.children !== n1.children) {
        const anchor = hostNextSibling(n1.anchor);
        removeStaticNode(n1);
        [n2.el, n2.anchor] = hostInsertStaticContent(
          n2.children,
          container,
          anchor,
          namespace
        );
      } else {
        n2.el = n1.el;
        n2.anchor = n1.anchor;
      }
    };
    const moveStaticNode = ({ el, anchor }, container, nextSibling) => {
      let next;
      while (el && el !== anchor) {
        next = hostNextSibling(el);
        hostInsert(el, container, nextSibling);
        el = next;
      }
      hostInsert(anchor, container, nextSibling);
    };
    const removeStaticNode = ({ el, anchor }) => {
      let next;
      while (el && el !== anchor) {
        next = hostNextSibling(el);
        hostRemove(el);
        el = next;
      }
      hostRemove(anchor);
    };
    const processElement = (n1, n2, container, anchor, parentComponent, parentSuspense, namespace, slotScopeIds, optimized) => {
      if (n2.type === "svg") {
        namespace = "svg";
      } else if (n2.type === "math") {
        namespace = "mathml";
      }
      if (n1 == null) {
        mountElement(
          n2,
          container,
          anchor,
          parentComponent,
          parentSuspense,
          namespace,
          slotScopeIds,
          optimized
        );
      } else {
        patchElement(
          n1,
          n2,
          parentComponent,
          parentSuspense,
          namespace,
          slotScopeIds,
          optimized
        );
      }
    };
    const mountElement = (vnode, container, anchor, parentComponent, parentSuspense, namespace, slotScopeIds, optimized) => {
      let el;
      let vnodeHook;
      const { props, shapeFlag, transition, dirs } = vnode;
      el = vnode.el = hostCreateElement(
        vnode.type,
        namespace,
        props && props.is,
        props
      );
      if (shapeFlag & 8) {
        hostSetElementText(el, vnode.children);
      } else if (shapeFlag & 16) {
        mountChildren(
          vnode.children,
          el,
          null,
          parentComponent,
          parentSuspense,
          resolveChildrenNamespace(vnode, namespace),
          slotScopeIds,
          optimized
        );
      }
      if (dirs) {
        invokeDirectiveHook(vnode, null, parentComponent, "created");
      }
      setScopeId(el, vnode, vnode.scopeId, slotScopeIds, parentComponent);
      if (props) {
        for (const key in props) {
          if (key !== "value" && !isReservedProp(key)) {
            hostPatchProp(el, key, null, props[key], namespace, parentComponent);
          }
        }
        if ("value" in props) {
          hostPatchProp(el, "value", null, props.value, namespace);
        }
        if (vnodeHook = props.onVnodeBeforeMount) {
          invokeVNodeHook(vnodeHook, parentComponent, vnode);
        }
      }
      if (true) {
        def(el, "__vnode", vnode, true);
        def(el, "__vueParentComponent", parentComponent, true);
      }
      if (dirs) {
        invokeDirectiveHook(vnode, null, parentComponent, "beforeMount");
      }
      const needCallTransitionHooks = needTransition(parentSuspense, transition);
      if (needCallTransitionHooks) {
        transition.beforeEnter(el);
      }
      hostInsert(el, container, anchor);
      if ((vnodeHook = props && props.onVnodeMounted) || needCallTransitionHooks || dirs) {
        queuePostRenderEffect(() => {
          vnodeHook && invokeVNodeHook(vnodeHook, parentComponent, vnode);
          needCallTransitionHooks && transition.enter(el);
          dirs && invokeDirectiveHook(vnode, null, parentComponent, "mounted");
        }, parentSuspense);
      }
    };
    const setScopeId = (el, vnode, scopeId, slotScopeIds, parentComponent) => {
      if (scopeId) {
        hostSetScopeId(el, scopeId);
      }
      if (slotScopeIds) {
        for (let i = 0; i < slotScopeIds.length; i++) {
          hostSetScopeId(el, slotScopeIds[i]);
        }
      }
      if (parentComponent) {
        let subTree = parentComponent.subTree;
        if (subTree.patchFlag > 0 && subTree.patchFlag & 2048) {
          subTree = filterSingleRoot(subTree.children) || subTree;
        }
        if (vnode === subTree || isSuspense(subTree.type) && (subTree.ssContent === vnode || subTree.ssFallback === vnode)) {
          const parentVNode = parentComponent.vnode;
          setScopeId(
            el,
            parentVNode,
            parentVNode.scopeId,
            parentVNode.slotScopeIds,
            parentComponent.parent
          );
        }
      }
    };
    const mountChildren = (children, container, anchor, parentComponent, parentSuspense, namespace, slotScopeIds, optimized, start = 0) => {
      for (let i = start; i < children.length; i++) {
        const child = children[i] = optimized ? cloneIfMounted(children[i]) : normalizeVNode(children[i]);
        patch(
          null,
          child,
          container,
          anchor,
          parentComponent,
          parentSuspense,
          namespace,
          slotScopeIds,
          optimized
        );
      }
    };
    const patchElement = (n1, n2, parentComponent, parentSuspense, namespace, slotScopeIds, optimized) => {
      const el = n2.el = n1.el;
      if (true) {
        el.__vnode = n2;
      }
      let { patchFlag, dynamicChildren, dirs } = n2;
      patchFlag |= n1.patchFlag & 16;
      const oldProps = n1.props || EMPTY_OBJ;
      const newProps = n2.props || EMPTY_OBJ;
      let vnodeHook;
      parentComponent && toggleRecurse(parentComponent, false);
      if (vnodeHook = newProps.onVnodeBeforeUpdate) {
        invokeVNodeHook(vnodeHook, parentComponent, n2, n1);
      }
      if (dirs) {
        invokeDirectiveHook(n2, n1, parentComponent, "beforeUpdate");
      }
      parentComponent && toggleRecurse(parentComponent, true);
      if (isHmrUpdating) {
        patchFlag = 0;
        optimized = false;
        dynamicChildren = null;
      }
      if (oldProps.innerHTML && newProps.innerHTML == null || oldProps.textContent && newProps.textContent == null) {
        hostSetElementText(el, "");
      }
      if (dynamicChildren) {
        patchBlockChildren(
          n1.dynamicChildren,
          dynamicChildren,
          el,
          parentComponent,
          parentSuspense,
          resolveChildrenNamespace(n2, namespace),
          slotScopeIds
        );
        if (true) {
          traverseStaticChildren(n1, n2);
        }
      } else if (!optimized) {
        patchChildren(
          n1,
          n2,
          el,
          null,
          parentComponent,
          parentSuspense,
          resolveChildrenNamespace(n2, namespace),
          slotScopeIds,
          false
        );
      }
      if (patchFlag > 0) {
        if (patchFlag & 16) {
          patchProps(el, oldProps, newProps, parentComponent, namespace);
        } else {
          if (patchFlag & 2) {
            if (oldProps.class !== newProps.class) {
              hostPatchProp(el, "class", null, newProps.class, namespace);
            }
          }
          if (patchFlag & 4) {
            hostPatchProp(el, "style", oldProps.style, newProps.style, namespace);
          }
          if (patchFlag & 8) {
            const propsToUpdate = n2.dynamicProps;
            for (let i = 0; i < propsToUpdate.length; i++) {
              const key = propsToUpdate[i];
              const prev = oldProps[key];
              const next = newProps[key];
              if (next !== prev || key === "value") {
                hostPatchProp(el, key, prev, next, namespace, parentComponent);
              }
            }
          }
        }
        if (patchFlag & 1) {
          if (n1.children !== n2.children) {
            hostSetElementText(el, n2.children);
          }
        }
      } else if (!optimized && dynamicChildren == null) {
        patchProps(el, oldProps, newProps, parentComponent, namespace);
      }
      if ((vnodeHook = newProps.onVnodeUpdated) || dirs) {
        queuePostRenderEffect(() => {
          vnodeHook && invokeVNodeHook(vnodeHook, parentComponent, n2, n1);
          dirs && invokeDirectiveHook(n2, n1, parentComponent, "updated");
        }, parentSuspense);
      }
    };
    const patchBlockChildren = (oldChildren, newChildren, fallbackContainer, parentComponent, parentSuspense, namespace, slotScopeIds) => {
      for (let i = 0; i < newChildren.length; i++) {
        const oldVNode = oldChildren[i];
        const newVNode = newChildren[i];
        const container = (
          // oldVNode may be an errored async setup() component inside Suspense
          // which will not have a mounted element
          oldVNode.el && // - In the case of a Fragment, we need to provide the actual parent
          // of the Fragment itself so it can move its children.
          (oldVNode.type === Fragment || // - In the case of different nodes, there is going to be a replacement
          // which also requires the correct parent container
          !isSameVNodeType(oldVNode, newVNode) || // - In the case of a component, it could contain anything.
          oldVNode.shapeFlag & (6 | 64)) ? hostParentNode(oldVNode.el) : (
            // In other cases, the parent container is not actually used so we
            // just pass the block element here to avoid a DOM parentNode call.
            fallbackContainer
          )
        );
        patch(
          oldVNode,
          newVNode,
          container,
          null,
          parentComponent,
          parentSuspense,
          namespace,
          slotScopeIds,
          true
        );
      }
    };
    const patchProps = (el, oldProps, newProps, parentComponent, namespace) => {
      if (oldProps !== newProps) {
        if (oldProps !== EMPTY_OBJ) {
          for (const key in oldProps) {
            if (!isReservedProp(key) && !(key in newProps)) {
              hostPatchProp(
                el,
                key,
                oldProps[key],
                null,
                namespace,
                parentComponent
              );
            }
          }
        }
        for (const key in newProps) {
          if (isReservedProp(key))
            continue;
          const next = newProps[key];
          const prev = oldProps[key];
          if (next !== prev && key !== "value") {
            hostPatchProp(el, key, prev, next, namespace, parentComponent);
          }
        }
        if ("value" in newProps) {
          hostPatchProp(el, "value", oldProps.value, newProps.value, namespace);
        }
      }
    };
    const processFragment = (n1, n2, container, anchor, parentComponent, parentSuspense, namespace, slotScopeIds, optimized) => {
      const fragmentStartAnchor = n2.el = n1 ? n1.el : hostCreateText("");
      const fragmentEndAnchor = n2.anchor = n1 ? n1.anchor : hostCreateText("");
      let { patchFlag, dynamicChildren, slotScopeIds: fragmentSlotScopeIds } = n2;
      if (
        // #5523 dev root fragment may inherit directives
        isHmrUpdating || patchFlag & 2048
      ) {
        patchFlag = 0;
        optimized = false;
        dynamicChildren = null;
      }
      if (fragmentSlotScopeIds) {
        slotScopeIds = slotScopeIds ? slotScopeIds.concat(fragmentSlotScopeIds) : fragmentSlotScopeIds;
      }
      if (n1 == null) {
        hostInsert(fragmentStartAnchor, container, anchor);
        hostInsert(fragmentEndAnchor, container, anchor);
        mountChildren(
          // #10007
          // such fragment like `<></>` will be compiled into
          // a fragment which doesn't have a children.
          // In this case fallback to an empty array
          n2.children || [],
          container,
          fragmentEndAnchor,
          parentComponent,
          parentSuspense,
          namespace,
          slotScopeIds,
          optimized
        );
      } else {
        if (patchFlag > 0 && patchFlag & 64 && dynamicChildren && // #2715 the previous fragment could've been a BAILed one as a result
        // of renderSlot() with no valid children
        n1.dynamicChildren) {
          patchBlockChildren(
            n1.dynamicChildren,
            dynamicChildren,
            container,
            parentComponent,
            parentSuspense,
            namespace,
            slotScopeIds
          );
          if (true) {
            traverseStaticChildren(n1, n2);
          } else if (
            // #2080 if the stable fragment has a key, it's a <template v-for> that may
            //  get moved around. Make sure all root level vnodes inherit el.
            // #2134 or if it's a component root, it may also get moved around
            // as the component is being moved.
            n2.key != null || parentComponent && n2 === parentComponent.subTree
          ) {
            traverseStaticChildren(
              n1,
              n2,
              true
              /* shallow */
            );
          }
        } else {
          patchChildren(
            n1,
            n2,
            container,
            fragmentEndAnchor,
            parentComponent,
            parentSuspense,
            namespace,
            slotScopeIds,
            optimized
          );
        }
      }
    };
    const processComponent = (n1, n2, container, anchor, parentComponent, parentSuspense, namespace, slotScopeIds, optimized) => {
      n2.slotScopeIds = slotScopeIds;
      if (n1 == null) {
        if (n2.shapeFlag & 512) {
          parentComponent.ctx.activate(
            n2,
            container,
            anchor,
            namespace,
            optimized
          );
        } else {
          mountComponent(
            n2,
            container,
            anchor,
            parentComponent,
            parentSuspense,
            namespace,
            optimized
          );
        }
      } else {
        updateComponent(n1, n2, optimized);
      }
    };
    const mountComponent = (initialVNode, container, anchor, parentComponent, parentSuspense, namespace, optimized) => {
      const instance = initialVNode.component = createComponentInstance(
        initialVNode,
        parentComponent,
        parentSuspense
      );
      if (instance.type.__hmrId) {
        registerHMR(instance);
      }
      if (true) {
        pushWarningContext(initialVNode);
        startMeasure(instance, `mount`);
      }
      if (isKeepAlive(initialVNode)) {
        instance.ctx.renderer = internals;
      }
      {
        if (true) {
          startMeasure(instance, `init`);
        }
        setupComponent(instance, false, optimized);
        if (true) {
          endMeasure(instance, `init`);
        }
      }
      if (instance.asyncDep) {
        if (isHmrUpdating)
          initialVNode.el = null;
        parentSuspense && parentSuspense.registerDep(instance, setupRenderEffect, optimized);
        if (!initialVNode.el) {
          const placeholder = instance.subTree = createVNode(Comment);
          processCommentNode(null, placeholder, container, anchor);
        }
      } else {
        setupRenderEffect(
          instance,
          initialVNode,
          container,
          anchor,
          parentSuspense,
          namespace,
          optimized
        );
      }
      if (true) {
        popWarningContext();
        endMeasure(instance, `mount`);
      }
    };
    const updateComponent = (n1, n2, optimized) => {
      const instance = n2.component = n1.component;
      if (shouldUpdateComponent(n1, n2, optimized)) {
        if (instance.asyncDep && !instance.asyncResolved) {
          if (true) {
            pushWarningContext(n2);
          }
          updateComponentPreRender(instance, n2, optimized);
          if (true) {
            popWarningContext();
          }
          return;
        } else {
          instance.next = n2;
          instance.update();
        }
      } else {
        n2.el = n1.el;
        instance.vnode = n2;
      }
    };
    const setupRenderEffect = (instance, initialVNode, container, anchor, parentSuspense, namespace, optimized) => {
      const componentUpdateFn = () => {
        if (!instance.isMounted) {
          let vnodeHook;
          const { el, props } = initialVNode;
          const { bm, m, parent, root, type } = instance;
          const isAsyncWrapperVNode = isAsyncWrapper(initialVNode);
          toggleRecurse(instance, false);
          if (bm) {
            invokeArrayFns(bm);
          }
          if (!isAsyncWrapperVNode && (vnodeHook = props && props.onVnodeBeforeMount)) {
            invokeVNodeHook(vnodeHook, parent, initialVNode);
          }
          toggleRecurse(instance, true);
          if (el && hydrateNode) {
            const hydrateSubTree = () => {
              if (true) {
                startMeasure(instance, `render`);
              }
              instance.subTree = renderComponentRoot(instance);
              if (true) {
                endMeasure(instance, `render`);
              }
              if (true) {
                startMeasure(instance, `hydrate`);
              }
              hydrateNode(
                el,
                instance.subTree,
                instance,
                parentSuspense,
                null
              );
              if (true) {
                endMeasure(instance, `hydrate`);
              }
            };
            if (isAsyncWrapperVNode && type.__asyncHydrate) {
              type.__asyncHydrate(
                el,
                instance,
                hydrateSubTree
              );
            } else {
              hydrateSubTree();
            }
          } else {
            if (root.ce) {
              root.ce._injectChildStyle(type);
            }
            if (true) {
              startMeasure(instance, `render`);
            }
            const subTree = instance.subTree = renderComponentRoot(instance);
            if (true) {
              endMeasure(instance, `render`);
            }
            if (true) {
              startMeasure(instance, `patch`);
            }
            patch(
              null,
              subTree,
              container,
              anchor,
              instance,
              parentSuspense,
              namespace
            );
            if (true) {
              endMeasure(instance, `patch`);
            }
            initialVNode.el = subTree.el;
          }
          if (m) {
            queuePostRenderEffect(m, parentSuspense);
          }
          if (!isAsyncWrapperVNode && (vnodeHook = props && props.onVnodeMounted)) {
            const scopedInitialVNode = initialVNode;
            queuePostRenderEffect(
              () => invokeVNodeHook(vnodeHook, parent, scopedInitialVNode),
              parentSuspense
            );
          }
          if (initialVNode.shapeFlag & 256 || parent && isAsyncWrapper(parent.vnode) && parent.vnode.shapeFlag & 256) {
            instance.a && queuePostRenderEffect(instance.a, parentSuspense);
          }
          instance.isMounted = true;
          if (true) {
            devtoolsComponentAdded(instance);
          }
          initialVNode = container = anchor = null;
        } else {
          let { next, bu, u, parent, vnode } = instance;
          {
            const nonHydratedAsyncRoot = locateNonHydratedAsyncRoot(instance);
            if (nonHydratedAsyncRoot) {
              if (next) {
                next.el = vnode.el;
                updateComponentPreRender(instance, next, optimized);
              }
              nonHydratedAsyncRoot.asyncDep.then(() => {
                if (!instance.isUnmounted) {
                  componentUpdateFn();
                }
              });
              return;
            }
          }
          let originNext = next;
          let vnodeHook;
          if (true) {
            pushWarningContext(next || instance.vnode);
          }
          toggleRecurse(instance, false);
          if (next) {
            next.el = vnode.el;
            updateComponentPreRender(instance, next, optimized);
          } else {
            next = vnode;
          }
          if (bu) {
            invokeArrayFns(bu);
          }
          if (vnodeHook = next.props && next.props.onVnodeBeforeUpdate) {
            invokeVNodeHook(vnodeHook, parent, next, vnode);
          }
          toggleRecurse(instance, true);
          if (true) {
            startMeasure(instance, `render`);
          }
          const nextTree = renderComponentRoot(instance);
          if (true) {
            endMeasure(instance, `render`);
          }
          const prevTree = instance.subTree;
          instance.subTree = nextTree;
          if (true) {
            startMeasure(instance, `patch`);
          }
          patch(
            prevTree,
            nextTree,
            // parent may have changed if it's in a teleport
            hostParentNode(prevTree.el),
            // anchor may have changed if it's in a fragment
            getNextHostNode(prevTree),
            instance,
            parentSuspense,
            namespace
          );
          if (true) {
            endMeasure(instance, `patch`);
          }
          next.el = nextTree.el;
          if (originNext === null) {
            updateHOCHostEl(instance, nextTree.el);
          }
          if (u) {
            queuePostRenderEffect(u, parentSuspense);
          }
          if (vnodeHook = next.props && next.props.onVnodeUpdated) {
            queuePostRenderEffect(
              () => invokeVNodeHook(vnodeHook, parent, next, vnode),
              parentSuspense
            );
          }
          if (true) {
            devtoolsComponentUpdated(instance);
          }
          if (true) {
            popWarningContext();
          }
        }
      };
      instance.scope.on();
      const effect2 = instance.effect = new ReactiveEffect(componentUpdateFn);
      instance.scope.off();
      const update = instance.update = effect2.run.bind(effect2);
      const job = instance.job = effect2.runIfDirty.bind(effect2);
      job.i = instance;
      job.id = instance.uid;
      effect2.scheduler = () => queueJob(job);
      toggleRecurse(instance, true);
      if (true) {
        effect2.onTrack = instance.rtc ? (e) => invokeArrayFns(instance.rtc, e) : void 0;
        effect2.onTrigger = instance.rtg ? (e) => invokeArrayFns(instance.rtg, e) : void 0;
      }
      update();
    };
    const updateComponentPreRender = (instance, nextVNode, optimized) => {
      nextVNode.component = instance;
      const prevProps = instance.vnode.props;
      instance.vnode = nextVNode;
      instance.next = null;
      updateProps(instance, nextVNode.props, prevProps, optimized);
      updateSlots(instance, nextVNode.children, optimized);
      pauseTracking();
      flushPreFlushCbs(instance);
      resetTracking();
    };
    const patchChildren = (n1, n2, container, anchor, parentComponent, parentSuspense, namespace, slotScopeIds, optimized = false) => {
      const c1 = n1 && n1.children;
      const prevShapeFlag = n1 ? n1.shapeFlag : 0;
      const c2 = n2.children;
      const { patchFlag, shapeFlag } = n2;
      if (patchFlag > 0) {
        if (patchFlag & 128) {
          patchKeyedChildren(
            c1,
            c2,
            container,
            anchor,
            parentComponent,
            parentSuspense,
            namespace,
            slotScopeIds,
            optimized
          );
          return;
        } else if (patchFlag & 256) {
          patchUnkeyedChildren(
            c1,
            c2,
            container,
            anchor,
            parentComponent,
            parentSuspense,
            namespace,
            slotScopeIds,
            optimized
          );
          return;
        }
      }
      if (shapeFlag & 8) {
        if (prevShapeFlag & 16) {
          unmountChildren(c1, parentComponent, parentSuspense);
        }
        if (c2 !== c1) {
          hostSetElementText(container, c2);
        }
      } else {
        if (prevShapeFlag & 16) {
          if (shapeFlag & 16) {
            patchKeyedChildren(
              c1,
              c2,
              container,
              anchor,
              parentComponent,
              parentSuspense,
              namespace,
              slotScopeIds,
              optimized
            );
          } else {
            unmountChildren(c1, parentComponent, parentSuspense, true);
          }
        } else {
          if (prevShapeFlag & 8) {
            hostSetElementText(container, "");
          }
          if (shapeFlag & 16) {
            mountChildren(
              c2,
              container,
              anchor,
              parentComponent,
              parentSuspense,
              namespace,
              slotScopeIds,
              optimized
            );
          }
        }
      }
    };
    const patchUnkeyedChildren = (c1, c2, container, anchor, parentComponent, parentSuspense, namespace, slotScopeIds, optimized) => {
      c1 = c1 || EMPTY_ARR;
      c2 = c2 || EMPTY_ARR;
      const oldLength = c1.length;
      const newLength = c2.length;
      const commonLength = Math.min(oldLength, newLength);
      let i;
      for (i = 0; i < commonLength; i++) {
        const nextChild = c2[i] = optimized ? cloneIfMounted(c2[i]) : normalizeVNode(c2[i]);
        patch(
          c1[i],
          nextChild,
          container,
          null,
          parentComponent,
          parentSuspense,
          namespace,
          slotScopeIds,
          optimized
        );
      }
      if (oldLength > newLength) {
        unmountChildren(
          c1,
          parentComponent,
          parentSuspense,
          true,
          false,
          commonLength
        );
      } else {
        mountChildren(
          c2,
          container,
          anchor,
          parentComponent,
          parentSuspense,
          namespace,
          slotScopeIds,
          optimized,
          commonLength
        );
      }
    };
    const patchKeyedChildren = (c1, c2, container, parentAnchor, parentComponent, parentSuspense, namespace, slotScopeIds, optimized) => {
      let i = 0;
      const l2 = c2.length;
      let e1 = c1.length - 1;
      let e2 = l2 - 1;
      while (i <= e1 && i <= e2) {
        const n1 = c1[i];
        const n2 = c2[i] = optimized ? cloneIfMounted(c2[i]) : normalizeVNode(c2[i]);
        if (isSameVNodeType(n1, n2)) {
          patch(
            n1,
            n2,
            container,
            null,
            parentComponent,
            parentSuspense,
            namespace,
            slotScopeIds,
            optimized
          );
        } else {
          break;
        }
        i++;
      }
      while (i <= e1 && i <= e2) {
        const n1 = c1[e1];
        const n2 = c2[e2] = optimized ? cloneIfMounted(c2[e2]) : normalizeVNode(c2[e2]);
        if (isSameVNodeType(n1, n2)) {
          patch(
            n1,
            n2,
            container,
            null,
            parentComponent,
            parentSuspense,
            namespace,
            slotScopeIds,
            optimized
          );
        } else {
          break;
        }
        e1--;
        e2--;
      }
      if (i > e1) {
        if (i <= e2) {
          const nextPos = e2 + 1;
          const anchor = nextPos < l2 ? c2[nextPos].el : parentAnchor;
          while (i <= e2) {
            patch(
              null,
              c2[i] = optimized ? cloneIfMounted(c2[i]) : normalizeVNode(c2[i]),
              container,
              anchor,
              parentComponent,
              parentSuspense,
              namespace,
              slotScopeIds,
              optimized
            );
            i++;
          }
        }
      } else if (i > e2) {
        while (i <= e1) {
          unmount(c1[i], parentComponent, parentSuspense, true);
          i++;
        }
      } else {
        const s1 = i;
        const s2 = i;
        const keyToNewIndexMap = /* @__PURE__ */ new Map();
        for (i = s2; i <= e2; i++) {
          const nextChild = c2[i] = optimized ? cloneIfMounted(c2[i]) : normalizeVNode(c2[i]);
          if (nextChild.key != null) {
            if (keyToNewIndexMap.has(nextChild.key)) {
              warn$1(
                `Duplicate keys found during update:`,
                JSON.stringify(nextChild.key),
                `Make sure keys are unique.`
              );
            }
            keyToNewIndexMap.set(nextChild.key, i);
          }
        }
        let j;
        let patched = 0;
        const toBePatched = e2 - s2 + 1;
        let moved = false;
        let maxNewIndexSoFar = 0;
        const newIndexToOldIndexMap = new Array(toBePatched);
        for (i = 0; i < toBePatched; i++)
          newIndexToOldIndexMap[i] = 0;
        for (i = s1; i <= e1; i++) {
          const prevChild = c1[i];
          if (patched >= toBePatched) {
            unmount(prevChild, parentComponent, parentSuspense, true);
            continue;
          }
          let newIndex;
          if (prevChild.key != null) {
            newIndex = keyToNewIndexMap.get(prevChild.key);
          } else {
            for (j = s2; j <= e2; j++) {
              if (newIndexToOldIndexMap[j - s2] === 0 && isSameVNodeType(prevChild, c2[j])) {
                newIndex = j;
                break;
              }
            }
          }
          if (newIndex === void 0) {
            unmount(prevChild, parentComponent, parentSuspense, true);
          } else {
            newIndexToOldIndexMap[newIndex - s2] = i + 1;
            if (newIndex >= maxNewIndexSoFar) {
              maxNewIndexSoFar = newIndex;
            } else {
              moved = true;
            }
            patch(
              prevChild,
              c2[newIndex],
              container,
              null,
              parentComponent,
              parentSuspense,
              namespace,
              slotScopeIds,
              optimized
            );
            patched++;
          }
        }
        const increasingNewIndexSequence = moved ? getSequence(newIndexToOldIndexMap) : EMPTY_ARR;
        j = increasingNewIndexSequence.length - 1;
        for (i = toBePatched - 1; i >= 0; i--) {
          const nextIndex = s2 + i;
          const nextChild = c2[nextIndex];
          const anchor = nextIndex + 1 < l2 ? c2[nextIndex + 1].el : parentAnchor;
          if (newIndexToOldIndexMap[i] === 0) {
            patch(
              null,
              nextChild,
              container,
              anchor,
              parentComponent,
              parentSuspense,
              namespace,
              slotScopeIds,
              optimized
            );
          } else if (moved) {
            if (j < 0 || i !== increasingNewIndexSequence[j]) {
              move(nextChild, container, anchor, 2);
            } else {
              j--;
            }
          }
        }
      }
    };
    const move = (vnode, container, anchor, moveType, parentSuspense = null) => {
      const { el, type, transition, children, shapeFlag } = vnode;
      if (shapeFlag & 6) {
        move(vnode.component.subTree, container, anchor, moveType);
        return;
      }
      if (shapeFlag & 128) {
        vnode.suspense.move(container, anchor, moveType);
        return;
      }
      if (shapeFlag & 64) {
        type.move(vnode, container, anchor, internals);
        return;
      }
      if (type === Fragment) {
        hostInsert(el, container, anchor);
        for (let i = 0; i < children.length; i++) {
          move(children[i], container, anchor, moveType);
        }
        hostInsert(vnode.anchor, container, anchor);
        return;
      }
      if (type === Static) {
        moveStaticNode(vnode, container, anchor);
        return;
      }
      const needTransition2 = moveType !== 2 && shapeFlag & 1 && transition;
      if (needTransition2) {
        if (moveType === 0) {
          transition.beforeEnter(el);
          hostInsert(el, container, anchor);
          queuePostRenderEffect(() => transition.enter(el), parentSuspense);
        } else {
          const { leave, delayLeave, afterLeave } = transition;
          const remove22 = () => hostInsert(el, container, anchor);
          const performLeave = () => {
            leave(el, () => {
              remove22();
              afterLeave && afterLeave();
            });
          };
          if (delayLeave) {
            delayLeave(el, remove22, performLeave);
          } else {
            performLeave();
          }
        }
      } else {
        hostInsert(el, container, anchor);
      }
    };
    const unmount = (vnode, parentComponent, parentSuspense, doRemove = false, optimized = false) => {
      const {
        type,
        props,
        ref: ref2,
        children,
        dynamicChildren,
        shapeFlag,
        patchFlag,
        dirs,
        cacheIndex
      } = vnode;
      if (patchFlag === -2) {
        optimized = false;
      }
      if (ref2 != null) {
        setRef(ref2, null, parentSuspense, vnode, true);
      }
      if (cacheIndex != null) {
        parentComponent.renderCache[cacheIndex] = void 0;
      }
      if (shapeFlag & 256) {
        parentComponent.ctx.deactivate(vnode);
        return;
      }
      const shouldInvokeDirs = shapeFlag & 1 && dirs;
      const shouldInvokeVnodeHook = !isAsyncWrapper(vnode);
      let vnodeHook;
      if (shouldInvokeVnodeHook && (vnodeHook = props && props.onVnodeBeforeUnmount)) {
        invokeVNodeHook(vnodeHook, parentComponent, vnode);
      }
      if (shapeFlag & 6) {
        unmountComponent(vnode.component, parentSuspense, doRemove);
      } else {
        if (shapeFlag & 128) {
          vnode.suspense.unmount(parentSuspense, doRemove);
          return;
        }
        if (shouldInvokeDirs) {
          invokeDirectiveHook(vnode, null, parentComponent, "beforeUnmount");
        }
        if (shapeFlag & 64) {
          vnode.type.remove(
            vnode,
            parentComponent,
            parentSuspense,
            internals,
            doRemove
          );
        } else if (dynamicChildren && // #5154
        // when v-once is used inside a block, setBlockTracking(-1) marks the
        // parent block with hasOnce: true
        // so that it doesn't take the fast path during unmount - otherwise
        // components nested in v-once are never unmounted.
        !dynamicChildren.hasOnce && // #1153: fast path should not be taken for non-stable (v-for) fragments
        (type !== Fragment || patchFlag > 0 && patchFlag & 64)) {
          unmountChildren(
            dynamicChildren,
            parentComponent,
            parentSuspense,
            false,
            true
          );
        } else if (type === Fragment && patchFlag & (128 | 256) || !optimized && shapeFlag & 16) {
          unmountChildren(children, parentComponent, parentSuspense);
        }
        if (doRemove) {
          remove2(vnode);
        }
      }
      if (shouldInvokeVnodeHook && (vnodeHook = props && props.onVnodeUnmounted) || shouldInvokeDirs) {
        queuePostRenderEffect(() => {
          vnodeHook && invokeVNodeHook(vnodeHook, parentComponent, vnode);
          shouldInvokeDirs && invokeDirectiveHook(vnode, null, parentComponent, "unmounted");
        }, parentSuspense);
      }
    };
    const remove2 = (vnode) => {
      const { type, el, anchor, transition } = vnode;
      if (type === Fragment) {
        if (vnode.patchFlag > 0 && vnode.patchFlag & 2048 && transition && !transition.persisted) {
          vnode.children.forEach((child) => {
            if (child.type === Comment) {
              hostRemove(child.el);
            } else {
              remove2(child);
            }
          });
        } else {
          removeFragment(el, anchor);
        }
        return;
      }
      if (type === Static) {
        removeStaticNode(vnode);
        return;
      }
      const performRemove = () => {
        hostRemove(el);
        if (transition && !transition.persisted && transition.afterLeave) {
          transition.afterLeave();
        }
      };
      if (vnode.shapeFlag & 1 && transition && !transition.persisted) {
        const { leave, delayLeave } = transition;
        const performLeave = () => leave(el, performRemove);
        if (delayLeave) {
          delayLeave(vnode.el, performRemove, performLeave);
        } else {
          performLeave();
        }
      } else {
        performRemove();
      }
    };
    const removeFragment = (cur, end) => {
      let next;
      while (cur !== end) {
        next = hostNextSibling(cur);
        hostRemove(cur);
        cur = next;
      }
      hostRemove(end);
    };
    const unmountComponent = (instance, parentSuspense, doRemove) => {
      if (instance.type.__hmrId) {
        unregisterHMR(instance);
      }
      const { bum, scope, job, subTree, um, m, a } = instance;
      invalidateMount(m);
      invalidateMount(a);
      if (bum) {
        invokeArrayFns(bum);
      }
      scope.stop();
      if (job) {
        job.flags |= 8;
        unmount(subTree, instance, parentSuspense, doRemove);
      }
      if (um) {
        queuePostRenderEffect(um, parentSuspense);
      }
      queuePostRenderEffect(() => {
        instance.isUnmounted = true;
      }, parentSuspense);
      if (parentSuspense && parentSuspense.pendingBranch && !parentSuspense.isUnmounted && instance.asyncDep && !instance.asyncResolved && instance.suspenseId === parentSuspense.pendingId) {
        parentSuspense.deps--;
        if (parentSuspense.deps === 0) {
          parentSuspense.resolve();
        }
      }
      if (true) {
        devtoolsComponentRemoved(instance);
      }
    };
    const unmountChildren = (children, parentComponent, parentSuspense, doRemove = false, optimized = false, start = 0) => {
      for (let i = start; i < children.length; i++) {
        unmount(children[i], parentComponent, parentSuspense, doRemove, optimized);
      }
    };
    const getNextHostNode = (vnode) => {
      if (vnode.shapeFlag & 6) {
        return getNextHostNode(vnode.component.subTree);
      }
      if (vnode.shapeFlag & 128) {
        return vnode.suspense.next();
      }
      const el = hostNextSibling(vnode.anchor || vnode.el);
      const teleportEnd = el && el[TeleportEndKey];
      return teleportEnd ? hostNextSibling(teleportEnd) : el;
    };
    let isFlushing = false;
    const render15 = (vnode, container, namespace) => {
      if (vnode == null) {
        if (container._vnode) {
          unmount(container._vnode, null, null, true);
        }
      } else {
        patch(
          container._vnode || null,
          vnode,
          container,
          null,
          null,
          null,
          namespace
        );
      }
      container._vnode = vnode;
      if (!isFlushing) {
        isFlushing = true;
        flushPreFlushCbs();
        flushPostFlushCbs();
        isFlushing = false;
      }
    };
    const internals = {
      p: patch,
      um: unmount,
      m: move,
      r: remove2,
      mt: mountComponent,
      mc: mountChildren,
      pc: patchChildren,
      pbc: patchBlockChildren,
      n: getNextHostNode,
      o: options
    };
    let hydrate;
    let hydrateNode;
    if (createHydrationFns) {
      [hydrate, hydrateNode] = createHydrationFns(
        internals
      );
    }
    return {
      render: render15,
      hydrate,
      createApp: createAppAPI(render15, hydrate)
    };
  }
  function resolveChildrenNamespace({ type, props }, currentNamespace) {
    return currentNamespace === "svg" && type === "foreignObject" || currentNamespace === "mathml" && type === "annotation-xml" && props && props.encoding && props.encoding.includes("html") ? void 0 : currentNamespace;
  }
  function toggleRecurse({ effect: effect2, job }, allowed) {
    if (allowed) {
      effect2.flags |= 32;
      job.flags |= 4;
    } else {
      effect2.flags &= ~32;
      job.flags &= ~4;
    }
  }
  function needTransition(parentSuspense, transition) {
    return (!parentSuspense || parentSuspense && !parentSuspense.pendingBranch) && transition && !transition.persisted;
  }
  function traverseStaticChildren(n1, n2, shallow = false) {
    const ch1 = n1.children;
    const ch2 = n2.children;
    if (isArray(ch1) && isArray(ch2)) {
      for (let i = 0; i < ch1.length; i++) {
        const c1 = ch1[i];
        let c2 = ch2[i];
        if (c2.shapeFlag & 1 && !c2.dynamicChildren) {
          if (c2.patchFlag <= 0 || c2.patchFlag === 32) {
            c2 = ch2[i] = cloneIfMounted(ch2[i]);
            c2.el = c1.el;
          }
          if (!shallow && c2.patchFlag !== -2)
            traverseStaticChildren(c1, c2);
        }
        if (c2.type === Text) {
          c2.el = c1.el;
        }
        if (c2.type === Comment && !c2.el) {
          c2.el = c1.el;
        }
      }
    }
  }
  function getSequence(arr) {
    const p2 = arr.slice();
    const result = [0];
    let i, j, u, v, c;
    const len = arr.length;
    for (i = 0; i < len; i++) {
      const arrI = arr[i];
      if (arrI !== 0) {
        j = result[result.length - 1];
        if (arr[j] < arrI) {
          p2[i] = j;
          result.push(i);
          continue;
        }
        u = 0;
        v = result.length - 1;
        while (u < v) {
          c = u + v >> 1;
          if (arr[result[c]] < arrI) {
            u = c + 1;
          } else {
            v = c;
          }
        }
        if (arrI < arr[result[u]]) {
          if (u > 0) {
            p2[i] = result[u - 1];
          }
          result[u] = i;
        }
      }
    }
    u = result.length;
    v = result[u - 1];
    while (u-- > 0) {
      result[u] = v;
      v = p2[v];
    }
    return result;
  }
  function locateNonHydratedAsyncRoot(instance) {
    const subComponent = instance.subTree.component;
    if (subComponent) {
      if (subComponent.asyncDep && !subComponent.asyncResolved) {
        return subComponent;
      } else {
        return locateNonHydratedAsyncRoot(subComponent);
      }
    }
  }
  function invalidateMount(hooks) {
    if (hooks) {
      for (let i = 0; i < hooks.length; i++)
        hooks[i].flags |= 8;
    }
  }
  var ssrContextKey = Symbol.for("v-scx");
  var useSSRContext = () => {
    {
      const ctx = inject(ssrContextKey);
      if (!ctx) {
        warn$1(
          `Server rendering context not provided. Make sure to only call useSSRContext() conditionally in the server build.`
        );
      }
      return ctx;
    }
  };
  function watch2(source, cb, options) {
    if (!isFunction(cb)) {
      warn$1(
        `\`watch(fn, options?)\` signature has been moved to a separate API. Use \`watchEffect(fn, options?)\` instead. \`watch\` now only supports \`watch(source, cb, options?) signature.`
      );
    }
    return doWatch(source, cb, options);
  }
  function doWatch(source, cb, options = EMPTY_OBJ) {
    const { immediate, deep, flush, once } = options;
    if (!cb) {
      if (immediate !== void 0) {
        warn$1(
          `watch() "immediate" option is only respected when using the watch(source, callback, options?) signature.`
        );
      }
      if (deep !== void 0) {
        warn$1(
          `watch() "deep" option is only respected when using the watch(source, callback, options?) signature.`
        );
      }
      if (once !== void 0) {
        warn$1(
          `watch() "once" option is only respected when using the watch(source, callback, options?) signature.`
        );
      }
    }
    const baseWatchOptions = extend({}, options);
    if (true)
      baseWatchOptions.onWarn = warn$1;
    const runsImmediately = cb && immediate || !cb && flush !== "post";
    let ssrCleanup;
    if (isInSSRComponentSetup) {
      if (flush === "sync") {
        const ctx = useSSRContext();
        ssrCleanup = ctx.__watcherHandles || (ctx.__watcherHandles = []);
      } else if (!runsImmediately) {
        const watchStopHandle = () => {
        };
        watchStopHandle.stop = NOOP;
        watchStopHandle.resume = NOOP;
        watchStopHandle.pause = NOOP;
        return watchStopHandle;
      }
    }
    const instance = currentInstance;
    baseWatchOptions.call = (fn, type, args) => callWithAsyncErrorHandling(fn, instance, type, args);
    let isPre = false;
    if (flush === "post") {
      baseWatchOptions.scheduler = (job) => {
        queuePostRenderEffect(job, instance && instance.suspense);
      };
    } else if (flush !== "sync") {
      isPre = true;
      baseWatchOptions.scheduler = (job, isFirstRun) => {
        if (isFirstRun) {
          job();
        } else {
          queueJob(job);
        }
      };
    }
    baseWatchOptions.augmentJob = (job) => {
      if (cb) {
        job.flags |= 4;
      }
      if (isPre) {
        job.flags |= 2;
        if (instance) {
          job.id = instance.uid;
          job.i = instance;
        }
      }
    };
    const watchHandle = watch(source, cb, baseWatchOptions);
    if (isInSSRComponentSetup) {
      if (ssrCleanup) {
        ssrCleanup.push(watchHandle);
      } else if (runsImmediately) {
        watchHandle();
      }
    }
    return watchHandle;
  }
  function instanceWatch(source, value, options) {
    const publicThis = this.proxy;
    const getter = isString(source) ? source.includes(".") ? createPathGetter(publicThis, source) : () => publicThis[source] : source.bind(publicThis, publicThis);
    let cb;
    if (isFunction(value)) {
      cb = value;
    } else {
      cb = value.handler;
      options = value;
    }
    const reset = setCurrentInstance(this);
    const res = doWatch(getter, cb.bind(publicThis), options);
    reset();
    return res;
  }
  function createPathGetter(ctx, path) {
    const segments = path.split(".");
    return () => {
      let cur = ctx;
      for (let i = 0; i < segments.length && cur; i++) {
        cur = cur[segments[i]];
      }
      return cur;
    };
  }
  var getModelModifiers = (props, modelName) => {
    return modelName === "modelValue" || modelName === "model-value" ? props.modelModifiers : props[`${modelName}Modifiers`] || props[`${camelize(modelName)}Modifiers`] || props[`${hyphenate(modelName)}Modifiers`];
  };
  function emit(instance, event, ...rawArgs) {
    if (instance.isUnmounted)
      return;
    const props = instance.vnode.props || EMPTY_OBJ;
    if (true) {
      const {
        emitsOptions,
        propsOptions: [propsOptions]
      } = instance;
      if (emitsOptions) {
        if (!(event in emitsOptions) && true) {
          if (!propsOptions || !(toHandlerKey(camelize(event)) in propsOptions)) {
            warn$1(
              `Component emitted event "${event}" but it is neither declared in the emits option nor as an "${toHandlerKey(camelize(event))}" prop.`
            );
          }
        } else {
          const validator = emitsOptions[event];
          if (isFunction(validator)) {
            const isValid = validator(...rawArgs);
            if (!isValid) {
              warn$1(
                `Invalid event arguments: event validation failed for event "${event}".`
              );
            }
          }
        }
      }
    }
    let args = rawArgs;
    const isModelListener2 = event.startsWith("update:");
    const modifiers = isModelListener2 && getModelModifiers(props, event.slice(7));
    if (modifiers) {
      if (modifiers.trim) {
        args = rawArgs.map((a) => isString(a) ? a.trim() : a);
      }
      if (modifiers.number) {
        args = rawArgs.map(looseToNumber);
      }
    }
    if (true) {
      devtoolsComponentEmit(instance, event, args);
    }
    if (true) {
      const lowerCaseEvent = event.toLowerCase();
      if (lowerCaseEvent !== event && props[toHandlerKey(lowerCaseEvent)]) {
        warn$1(
          `Event "${lowerCaseEvent}" is emitted in component ${formatComponentName(
            instance,
            instance.type
          )} but the handler is registered for "${event}". Note that HTML attributes are case-insensitive and you cannot use v-on to listen to camelCase events when using in-DOM templates. You should probably use "${hyphenate(
            event
          )}" instead of "${event}".`
        );
      }
    }
    let handlerName;
    let handler = props[handlerName = toHandlerKey(event)] || // also try camelCase event handler (#2249)
    props[handlerName = toHandlerKey(camelize(event))];
    if (!handler && isModelListener2) {
      handler = props[handlerName = toHandlerKey(hyphenate(event))];
    }
    if (handler) {
      callWithAsyncErrorHandling(
        handler,
        instance,
        6,
        args
      );
    }
    const onceHandler = props[handlerName + `Once`];
    if (onceHandler) {
      if (!instance.emitted) {
        instance.emitted = {};
      } else if (instance.emitted[handlerName]) {
        return;
      }
      instance.emitted[handlerName] = true;
      callWithAsyncErrorHandling(
        onceHandler,
        instance,
        6,
        args
      );
    }
  }
  function normalizeEmitsOptions(comp, appContext, asMixin = false) {
    const cache = appContext.emitsCache;
    const cached = cache.get(comp);
    if (cached !== void 0) {
      return cached;
    }
    const raw = comp.emits;
    let normalized = {};
    let hasExtends = false;
    if (!isFunction(comp)) {
      const extendEmits = (raw2) => {
        const normalizedFromExtend = normalizeEmitsOptions(raw2, appContext, true);
        if (normalizedFromExtend) {
          hasExtends = true;
          extend(normalized, normalizedFromExtend);
        }
      };
      if (!asMixin && appContext.mixins.length) {
        appContext.mixins.forEach(extendEmits);
      }
      if (comp.extends) {
        extendEmits(comp.extends);
      }
      if (comp.mixins) {
        comp.mixins.forEach(extendEmits);
      }
    }
    if (!raw && !hasExtends) {
      if (isObject(comp)) {
        cache.set(comp, null);
      }
      return null;
    }
    if (isArray(raw)) {
      raw.forEach((key) => normalized[key] = null);
    } else {
      extend(normalized, raw);
    }
    if (isObject(comp)) {
      cache.set(comp, normalized);
    }
    return normalized;
  }
  function isEmitListener(options, key) {
    if (!options || !isOn(key)) {
      return false;
    }
    key = key.slice(2).replace(/Once$/, "");
    return hasOwn(options, key[0].toLowerCase() + key.slice(1)) || hasOwn(options, hyphenate(key)) || hasOwn(options, key);
  }
  var accessedAttrs = false;
  function markAttrsAccessed() {
    accessedAttrs = true;
  }
  function renderComponentRoot(instance) {
    const {
      type: Component,
      vnode,
      proxy,
      withProxy,
      propsOptions: [propsOptions],
      slots,
      attrs,
      emit: emit2,
      render: render15,
      renderCache,
      props,
      data,
      setupState,
      ctx,
      inheritAttrs
    } = instance;
    const prev = setCurrentRenderingInstance(instance);
    let result;
    let fallthroughAttrs;
    if (true) {
      accessedAttrs = false;
    }
    try {
      if (vnode.shapeFlag & 4) {
        const proxyToUse = withProxy || proxy;
        const thisProxy = setupState.__isScriptSetup ? new Proxy(proxyToUse, {
          get(target, key, receiver) {
            warn$1(
              `Property '${String(
                key
              )}' was accessed via 'this'. Avoid using 'this' in templates.`
            );
            return Reflect.get(target, key, receiver);
          }
        }) : proxyToUse;
        result = normalizeVNode(
          render15.call(
            thisProxy,
            proxyToUse,
            renderCache,
            true ? shallowReadonly(props) : props,
            setupState,
            data,
            ctx
          )
        );
        fallthroughAttrs = attrs;
      } else {
        const render22 = Component;
        if (attrs === props) {
          markAttrsAccessed();
        }
        result = normalizeVNode(
          render22.length > 1 ? render22(
            true ? shallowReadonly(props) : props,
            true ? {
              get attrs() {
                markAttrsAccessed();
                return shallowReadonly(attrs);
              },
              slots,
              emit: emit2
            } : { attrs, slots, emit: emit2 }
          ) : render22(
            true ? shallowReadonly(props) : props,
            null
          )
        );
        fallthroughAttrs = Component.props ? attrs : getFunctionalFallthrough(attrs);
      }
    } catch (err) {
      blockStack.length = 0;
      handleError(err, instance, 1);
      result = createVNode(Comment);
    }
    let root = result;
    let setRoot = void 0;
    if (result.patchFlag > 0 && result.patchFlag & 2048) {
      [root, setRoot] = getChildRoot(result);
    }
    if (fallthroughAttrs && inheritAttrs !== false) {
      const keys = Object.keys(fallthroughAttrs);
      const { shapeFlag } = root;
      if (keys.length) {
        if (shapeFlag & (1 | 6)) {
          if (propsOptions && keys.some(isModelListener)) {
            fallthroughAttrs = filterModelListeners(
              fallthroughAttrs,
              propsOptions
            );
          }
          root = cloneVNode(root, fallthroughAttrs, false, true);
        } else if (!accessedAttrs && root.type !== Comment) {
          const allAttrs = Object.keys(attrs);
          const eventAttrs = [];
          const extraAttrs = [];
          for (let i = 0, l = allAttrs.length; i < l; i++) {
            const key = allAttrs[i];
            if (isOn(key)) {
              if (!isModelListener(key)) {
                eventAttrs.push(key[2].toLowerCase() + key.slice(3));
              }
            } else {
              extraAttrs.push(key);
            }
          }
          if (extraAttrs.length) {
            warn$1(
              `Extraneous non-props attributes (${extraAttrs.join(", ")}) were passed to component but could not be automatically inherited because component renders fragment or text or teleport root nodes.`
            );
          }
          if (eventAttrs.length) {
            warn$1(
              `Extraneous non-emits event listeners (${eventAttrs.join(", ")}) were passed to component but could not be automatically inherited because component renders fragment or text root nodes. If the listener is intended to be a component custom event listener only, declare it using the "emits" option.`
            );
          }
        }
      }
    }
    if (vnode.dirs) {
      if (!isElementRoot(root)) {
        warn$1(
          `Runtime directive used on component with non-element root node. The directives will not function as intended.`
        );
      }
      root = cloneVNode(root, null, false, true);
      root.dirs = root.dirs ? root.dirs.concat(vnode.dirs) : vnode.dirs;
    }
    if (vnode.transition) {
      if (!isElementRoot(root)) {
        warn$1(
          `Component inside <Transition> renders non-element root node that cannot be animated.`
        );
      }
      setTransitionHooks(root, vnode.transition);
    }
    if (setRoot) {
      setRoot(root);
    } else {
      result = root;
    }
    setCurrentRenderingInstance(prev);
    return result;
  }
  var getChildRoot = (vnode) => {
    const rawChildren = vnode.children;
    const dynamicChildren = vnode.dynamicChildren;
    const childRoot = filterSingleRoot(rawChildren, false);
    if (!childRoot) {
      return [vnode, void 0];
    } else if (childRoot.patchFlag > 0 && childRoot.patchFlag & 2048) {
      return getChildRoot(childRoot);
    }
    const index = rawChildren.indexOf(childRoot);
    const dynamicIndex = dynamicChildren ? dynamicChildren.indexOf(childRoot) : -1;
    const setRoot = (updatedRoot) => {
      rawChildren[index] = updatedRoot;
      if (dynamicChildren) {
        if (dynamicIndex > -1) {
          dynamicChildren[dynamicIndex] = updatedRoot;
        } else if (updatedRoot.patchFlag > 0) {
          vnode.dynamicChildren = [...dynamicChildren, updatedRoot];
        }
      }
    };
    return [normalizeVNode(childRoot), setRoot];
  };
  function filterSingleRoot(children, recurse = true) {
    let singleRoot;
    for (let i = 0; i < children.length; i++) {
      const child = children[i];
      if (isVNode(child)) {
        if (child.type !== Comment || child.children === "v-if") {
          if (singleRoot) {
            return;
          } else {
            singleRoot = child;
            if (recurse && singleRoot.patchFlag > 0 && singleRoot.patchFlag & 2048) {
              return filterSingleRoot(singleRoot.children);
            }
          }
        }
      } else {
        return;
      }
    }
    return singleRoot;
  }
  var getFunctionalFallthrough = (attrs) => {
    let res;
    for (const key in attrs) {
      if (key === "class" || key === "style" || isOn(key)) {
        (res || (res = {}))[key] = attrs[key];
      }
    }
    return res;
  };
  var filterModelListeners = (attrs, props) => {
    const res = {};
    for (const key in attrs) {
      if (!isModelListener(key) || !(key.slice(9) in props)) {
        res[key] = attrs[key];
      }
    }
    return res;
  };
  var isElementRoot = (vnode) => {
    return vnode.shapeFlag & (6 | 1) || vnode.type === Comment;
  };
  function shouldUpdateComponent(prevVNode, nextVNode, optimized) {
    const { props: prevProps, children: prevChildren, component } = prevVNode;
    const { props: nextProps, children: nextChildren, patchFlag } = nextVNode;
    const emits = component.emitsOptions;
    if ((prevChildren || nextChildren) && isHmrUpdating) {
      return true;
    }
    if (nextVNode.dirs || nextVNode.transition) {
      return true;
    }
    if (optimized && patchFlag >= 0) {
      if (patchFlag & 1024) {
        return true;
      }
      if (patchFlag & 16) {
        if (!prevProps) {
          return !!nextProps;
        }
        return hasPropsChanged(prevProps, nextProps, emits);
      } else if (patchFlag & 8) {
        const dynamicProps = nextVNode.dynamicProps;
        for (let i = 0; i < dynamicProps.length; i++) {
          const key = dynamicProps[i];
          if (nextProps[key] !== prevProps[key] && !isEmitListener(emits, key)) {
            return true;
          }
        }
      }
    } else {
      if (prevChildren || nextChildren) {
        if (!nextChildren || !nextChildren.$stable) {
          return true;
        }
      }
      if (prevProps === nextProps) {
        return false;
      }
      if (!prevProps) {
        return !!nextProps;
      }
      if (!nextProps) {
        return true;
      }
      return hasPropsChanged(prevProps, nextProps, emits);
    }
    return false;
  }
  function hasPropsChanged(prevProps, nextProps, emitsOptions) {
    const nextKeys = Object.keys(nextProps);
    if (nextKeys.length !== Object.keys(prevProps).length) {
      return true;
    }
    for (let i = 0; i < nextKeys.length; i++) {
      const key = nextKeys[i];
      if (nextProps[key] !== prevProps[key] && !isEmitListener(emitsOptions, key)) {
        return true;
      }
    }
    return false;
  }
  function updateHOCHostEl({ vnode, parent }, el) {
    while (parent) {
      const root = parent.subTree;
      if (root.suspense && root.suspense.activeBranch === vnode) {
        root.el = vnode.el;
      }
      if (root === vnode) {
        (vnode = parent.vnode).el = el;
        parent = parent.parent;
      } else {
        break;
      }
    }
  }
  var isSuspense = (type) => type.__isSuspense;
  function queueEffectWithSuspense(fn, suspense) {
    if (suspense && suspense.pendingBranch) {
      if (isArray(fn)) {
        suspense.effects.push(...fn);
      } else {
        suspense.effects.push(fn);
      }
    } else {
      queuePostFlushCb(fn);
    }
  }
  var Fragment = Symbol.for("v-fgt");
  var Text = Symbol.for("v-txt");
  var Comment = Symbol.for("v-cmt");
  var Static = Symbol.for("v-stc");
  var blockStack = [];
  var currentBlock = null;
  function openBlock(disableTracking = false) {
    blockStack.push(currentBlock = disableTracking ? null : []);
  }
  function closeBlock() {
    blockStack.pop();
    currentBlock = blockStack[blockStack.length - 1] || null;
  }
  var isBlockTreeEnabled = 1;
  function setBlockTracking(value, inVOnce = false) {
    isBlockTreeEnabled += value;
    if (value < 0 && currentBlock && inVOnce) {
      currentBlock.hasOnce = true;
    }
  }
  function setupBlock(vnode) {
    vnode.dynamicChildren = isBlockTreeEnabled > 0 ? currentBlock || EMPTY_ARR : null;
    closeBlock();
    if (isBlockTreeEnabled > 0 && currentBlock) {
      currentBlock.push(vnode);
    }
    return vnode;
  }
  function createElementBlock(type, props, children, patchFlag, dynamicProps, shapeFlag) {
    return setupBlock(
      createBaseVNode(
        type,
        props,
        children,
        patchFlag,
        dynamicProps,
        shapeFlag,
        true
      )
    );
  }
  function createBlock(type, props, children, patchFlag, dynamicProps) {
    return setupBlock(
      createVNode(
        type,
        props,
        children,
        patchFlag,
        dynamicProps,
        true
      )
    );
  }
  function isVNode(value) {
    return value ? value.__v_isVNode === true : false;
  }
  function isSameVNodeType(n1, n2) {
    if (n2.shapeFlag & 6 && n1.component) {
      const dirtyInstances = hmrDirtyComponents.get(n2.type);
      if (dirtyInstances && dirtyInstances.has(n1.component)) {
        n1.shapeFlag &= ~256;
        n2.shapeFlag &= ~512;
        return false;
      }
    }
    return n1.type === n2.type && n1.key === n2.key;
  }
  var vnodeArgsTransformer;
  var createVNodeWithArgsTransform = (...args) => {
    return _createVNode(
      ...vnodeArgsTransformer ? vnodeArgsTransformer(args, currentRenderingInstance) : args
    );
  };
  var normalizeKey = ({ key }) => key != null ? key : null;
  var normalizeRef = ({
    ref: ref2,
    ref_key,
    ref_for
  }) => {
    if (typeof ref2 === "number") {
      ref2 = "" + ref2;
    }
    return ref2 != null ? isString(ref2) || isRef2(ref2) || isFunction(ref2) ? { i: currentRenderingInstance, r: ref2, k: ref_key, f: !!ref_for } : ref2 : null;
  };
  function createBaseVNode(type, props = null, children = null, patchFlag = 0, dynamicProps = null, shapeFlag = type === Fragment ? 0 : 1, isBlockNode = false, needFullChildrenNormalization = false) {
    const vnode = {
      __v_isVNode: true,
      __v_skip: true,
      type,
      props,
      key: props && normalizeKey(props),
      ref: props && normalizeRef(props),
      scopeId: currentScopeId,
      slotScopeIds: null,
      children,
      component: null,
      suspense: null,
      ssContent: null,
      ssFallback: null,
      dirs: null,
      transition: null,
      el: null,
      anchor: null,
      target: null,
      targetStart: null,
      targetAnchor: null,
      staticCount: 0,
      shapeFlag,
      patchFlag,
      dynamicProps,
      dynamicChildren: null,
      appContext: null,
      ctx: currentRenderingInstance
    };
    if (needFullChildrenNormalization) {
      normalizeChildren(vnode, children);
      if (shapeFlag & 128) {
        type.normalize(vnode);
      }
    } else if (children) {
      vnode.shapeFlag |= isString(children) ? 8 : 16;
    }
    if (vnode.key !== vnode.key) {
      warn$1(`VNode created with invalid key (NaN). VNode type:`, vnode.type);
    }
    if (isBlockTreeEnabled > 0 && // avoid a block node from tracking itself
    !isBlockNode && // has current parent block
    currentBlock && // presence of a patch flag indicates this node needs patching on updates.
    // component nodes also should always be patched, because even if the
    // component doesn't need to update, it needs to persist the instance on to
    // the next vnode so that it can be properly unmounted later.
    (vnode.patchFlag > 0 || shapeFlag & 6) && // the EVENTS flag is only for hydration and if it is the only flag, the
    // vnode should not be considered dynamic due to handler caching.
    vnode.patchFlag !== 32) {
      currentBlock.push(vnode);
    }
    return vnode;
  }
  var createVNode = true ? createVNodeWithArgsTransform : _createVNode;
  function _createVNode(type, props = null, children = null, patchFlag = 0, dynamicProps = null, isBlockNode = false) {
    if (!type || type === NULL_DYNAMIC_COMPONENT) {
      if (!type) {
        warn$1(`Invalid vnode type when creating vnode: ${type}.`);
      }
      type = Comment;
    }
    if (isVNode(type)) {
      const cloned = cloneVNode(
        type,
        props,
        true
        /* mergeRef: true */
      );
      if (children) {
        normalizeChildren(cloned, children);
      }
      if (isBlockTreeEnabled > 0 && !isBlockNode && currentBlock) {
        if (cloned.shapeFlag & 6) {
          currentBlock[currentBlock.indexOf(type)] = cloned;
        } else {
          currentBlock.push(cloned);
        }
      }
      cloned.patchFlag = -2;
      return cloned;
    }
    if (isClassComponent(type)) {
      type = type.__vccOpts;
    }
    if (props) {
      props = guardReactiveProps(props);
      let { class: klass, style } = props;
      if (klass && !isString(klass)) {
        props.class = normalizeClass(klass);
      }
      if (isObject(style)) {
        if (isProxy(style) && !isArray(style)) {
          style = extend({}, style);
        }
        props.style = normalizeStyle(style);
      }
    }
    const shapeFlag = isString(type) ? 1 : isSuspense(type) ? 128 : isTeleport(type) ? 64 : isObject(type) ? 4 : isFunction(type) ? 2 : 0;
    if (shapeFlag & 4 && isProxy(type)) {
      type = toRaw(type);
      warn$1(
        `Vue received a Component that was made a reactive object. This can lead to unnecessary performance overhead and should be avoided by marking the component with \`markRaw\` or using \`shallowRef\` instead of \`ref\`.`,
        `
Component that was made reactive: `,
        type
      );
    }
    return createBaseVNode(
      type,
      props,
      children,
      patchFlag,
      dynamicProps,
      shapeFlag,
      isBlockNode,
      true
    );
  }
  function guardReactiveProps(props) {
    if (!props)
      return null;
    return isProxy(props) || isInternalObject(props) ? extend({}, props) : props;
  }
  function cloneVNode(vnode, extraProps, mergeRef = false, cloneTransition = false) {
    const { props, ref: ref2, patchFlag, children, transition } = vnode;
    const mergedProps = extraProps ? mergeProps(props || {}, extraProps) : props;
    const cloned = {
      __v_isVNode: true,
      __v_skip: true,
      type: vnode.type,
      props: mergedProps,
      key: mergedProps && normalizeKey(mergedProps),
      ref: extraProps && extraProps.ref ? (
        // #2078 in the case of <component :is="vnode" ref="extra"/>
        // if the vnode itself already has a ref, cloneVNode will need to merge
        // the refs so the single vnode can be set on multiple refs
        mergeRef && ref2 ? isArray(ref2) ? ref2.concat(normalizeRef(extraProps)) : [ref2, normalizeRef(extraProps)] : normalizeRef(extraProps)
      ) : ref2,
      scopeId: vnode.scopeId,
      slotScopeIds: vnode.slotScopeIds,
      children: patchFlag === -1 && isArray(children) ? children.map(deepCloneVNode) : children,
      target: vnode.target,
      targetStart: vnode.targetStart,
      targetAnchor: vnode.targetAnchor,
      staticCount: vnode.staticCount,
      shapeFlag: vnode.shapeFlag,
      // if the vnode is cloned with extra props, we can no longer assume its
      // existing patch flag to be reliable and need to add the FULL_PROPS flag.
      // note: preserve flag for fragments since they use the flag for children
      // fast paths only.
      patchFlag: extraProps && vnode.type !== Fragment ? patchFlag === -1 ? 16 : patchFlag | 16 : patchFlag,
      dynamicProps: vnode.dynamicProps,
      dynamicChildren: vnode.dynamicChildren,
      appContext: vnode.appContext,
      dirs: vnode.dirs,
      transition,
      // These should technically only be non-null on mounted VNodes. However,
      // they *should* be copied for kept-alive vnodes. So we just always copy
      // them since them being non-null during a mount doesn't affect the logic as
      // they will simply be overwritten.
      component: vnode.component,
      suspense: vnode.suspense,
      ssContent: vnode.ssContent && cloneVNode(vnode.ssContent),
      ssFallback: vnode.ssFallback && cloneVNode(vnode.ssFallback),
      el: vnode.el,
      anchor: vnode.anchor,
      ctx: vnode.ctx,
      ce: vnode.ce
    };
    if (transition && cloneTransition) {
      setTransitionHooks(
        cloned,
        transition.clone(cloned)
      );
    }
    return cloned;
  }
  function deepCloneVNode(vnode) {
    const cloned = cloneVNode(vnode);
    if (isArray(vnode.children)) {
      cloned.children = vnode.children.map(deepCloneVNode);
    }
    return cloned;
  }
  function createTextVNode(text = " ", flag = 0) {
    return createVNode(Text, null, text, flag);
  }
  function createCommentVNode(text = "", asBlock = false) {
    return asBlock ? (openBlock(), createBlock(Comment, null, text)) : createVNode(Comment, null, text);
  }
  function normalizeVNode(child) {
    if (child == null || typeof child === "boolean") {
      return createVNode(Comment);
    } else if (isArray(child)) {
      return createVNode(
        Fragment,
        null,
        // #3666, avoid reference pollution when reusing vnode
        child.slice()
      );
    } else if (isVNode(child)) {
      return cloneIfMounted(child);
    } else {
      return createVNode(Text, null, String(child));
    }
  }
  function cloneIfMounted(child) {
    return child.el === null && child.patchFlag !== -1 || child.memo ? child : cloneVNode(child);
  }
  function normalizeChildren(vnode, children) {
    let type = 0;
    const { shapeFlag } = vnode;
    if (children == null) {
      children = null;
    } else if (isArray(children)) {
      type = 16;
    } else if (typeof children === "object") {
      if (shapeFlag & (1 | 64)) {
        const slot = children.default;
        if (slot) {
          slot._c && (slot._d = false);
          normalizeChildren(vnode, slot());
          slot._c && (slot._d = true);
        }
        return;
      } else {
        type = 32;
        const slotFlag = children._;
        if (!slotFlag && !isInternalObject(children)) {
          children._ctx = currentRenderingInstance;
        } else if (slotFlag === 3 && currentRenderingInstance) {
          if (currentRenderingInstance.slots._ === 1) {
            children._ = 1;
          } else {
            children._ = 2;
            vnode.patchFlag |= 1024;
          }
        }
      }
    } else if (isFunction(children)) {
      children = { default: children, _ctx: currentRenderingInstance };
      type = 32;
    } else {
      children = String(children);
      if (shapeFlag & 64) {
        type = 16;
        children = [createTextVNode(children)];
      } else {
        type = 8;
      }
    }
    vnode.children = children;
    vnode.shapeFlag |= type;
  }
  function mergeProps(...args) {
    const ret = {};
    for (let i = 0; i < args.length; i++) {
      const toMerge = args[i];
      for (const key in toMerge) {
        if (key === "class") {
          if (ret.class !== toMerge.class) {
            ret.class = normalizeClass([ret.class, toMerge.class]);
          }
        } else if (key === "style") {
          ret.style = normalizeStyle([ret.style, toMerge.style]);
        } else if (isOn(key)) {
          const existing = ret[key];
          const incoming = toMerge[key];
          if (incoming && existing !== incoming && !(isArray(existing) && existing.includes(incoming))) {
            ret[key] = existing ? [].concat(existing, incoming) : incoming;
          }
        } else if (key !== "") {
          ret[key] = toMerge[key];
        }
      }
    }
    return ret;
  }
  function invokeVNodeHook(hook, instance, vnode, prevVNode = null) {
    callWithAsyncErrorHandling(hook, instance, 7, [
      vnode,
      prevVNode
    ]);
  }
  var emptyAppContext = createAppContext();
  var uid = 0;
  function createComponentInstance(vnode, parent, suspense) {
    const type = vnode.type;
    const appContext = (parent ? parent.appContext : vnode.appContext) || emptyAppContext;
    const instance = {
      uid: uid++,
      vnode,
      type,
      parent,
      appContext,
      root: null,
      // to be immediately set
      next: null,
      subTree: null,
      // will be set synchronously right after creation
      effect: null,
      update: null,
      // will be set synchronously right after creation
      job: null,
      scope: new EffectScope(
        true
        /* detached */
      ),
      render: null,
      proxy: null,
      exposed: null,
      exposeProxy: null,
      withProxy: null,
      provides: parent ? parent.provides : Object.create(appContext.provides),
      ids: parent ? parent.ids : ["", 0, 0],
      accessCache: null,
      renderCache: [],
      // local resolved assets
      components: null,
      directives: null,
      // resolved props and emits options
      propsOptions: normalizePropsOptions(type, appContext),
      emitsOptions: normalizeEmitsOptions(type, appContext),
      // emit
      emit: null,
      // to be set immediately
      emitted: null,
      // props default value
      propsDefaults: EMPTY_OBJ,
      // inheritAttrs
      inheritAttrs: type.inheritAttrs,
      // state
      ctx: EMPTY_OBJ,
      data: EMPTY_OBJ,
      props: EMPTY_OBJ,
      attrs: EMPTY_OBJ,
      slots: EMPTY_OBJ,
      refs: EMPTY_OBJ,
      setupState: EMPTY_OBJ,
      setupContext: null,
      // suspense related
      suspense,
      suspenseId: suspense ? suspense.pendingId : 0,
      asyncDep: null,
      asyncResolved: false,
      // lifecycle hooks
      // not using enums here because it results in computed properties
      isMounted: false,
      isUnmounted: false,
      isDeactivated: false,
      bc: null,
      c: null,
      bm: null,
      m: null,
      bu: null,
      u: null,
      um: null,
      bum: null,
      da: null,
      a: null,
      rtg: null,
      rtc: null,
      ec: null,
      sp: null
    };
    if (true) {
      instance.ctx = createDevRenderContext(instance);
    } else {
      instance.ctx = { _: instance };
    }
    instance.root = parent ? parent.root : instance;
    instance.emit = emit.bind(null, instance);
    if (vnode.ce) {
      vnode.ce(instance);
    }
    return instance;
  }
  var currentInstance = null;
  var getCurrentInstance = () => currentInstance || currentRenderingInstance;
  var internalSetCurrentInstance;
  var setInSSRSetupState;
  {
    const g = getGlobalThis();
    const registerGlobalSetter = (key, setter) => {
      let setters;
      if (!(setters = g[key]))
        setters = g[key] = [];
      setters.push(setter);
      return (v) => {
        if (setters.length > 1)
          setters.forEach((set) => set(v));
        else
          setters[0](v);
      };
    };
    internalSetCurrentInstance = registerGlobalSetter(
      `__VUE_INSTANCE_SETTERS__`,
      (v) => currentInstance = v
    );
    setInSSRSetupState = registerGlobalSetter(
      `__VUE_SSR_SETTERS__`,
      (v) => isInSSRComponentSetup = v
    );
  }
  var setCurrentInstance = (instance) => {
    const prev = currentInstance;
    internalSetCurrentInstance(instance);
    instance.scope.on();
    return () => {
      instance.scope.off();
      internalSetCurrentInstance(prev);
    };
  };
  var unsetCurrentInstance = () => {
    currentInstance && currentInstance.scope.off();
    internalSetCurrentInstance(null);
  };
  var isBuiltInTag = /* @__PURE__ */ makeMap("slot,component");
  function validateComponentName(name, { isNativeTag }) {
    if (isBuiltInTag(name) || isNativeTag(name)) {
      warn$1(
        "Do not use built-in or reserved HTML elements as component id: " + name
      );
    }
  }
  function isStatefulComponent(instance) {
    return instance.vnode.shapeFlag & 4;
  }
  var isInSSRComponentSetup = false;
  function setupComponent(instance, isSSR = false, optimized = false) {
    isSSR && setInSSRSetupState(isSSR);
    const { props, children } = instance.vnode;
    const isStateful = isStatefulComponent(instance);
    initProps(instance, props, isStateful, isSSR);
    initSlots(instance, children, optimized);
    const setupResult = isStateful ? setupStatefulComponent(instance, isSSR) : void 0;
    isSSR && setInSSRSetupState(false);
    return setupResult;
  }
  function setupStatefulComponent(instance, isSSR) {
    var _a;
    const Component = instance.type;
    if (true) {
      if (Component.name) {
        validateComponentName(Component.name, instance.appContext.config);
      }
      if (Component.components) {
        const names = Object.keys(Component.components);
        for (let i = 0; i < names.length; i++) {
          validateComponentName(names[i], instance.appContext.config);
        }
      }
      if (Component.directives) {
        const names = Object.keys(Component.directives);
        for (let i = 0; i < names.length; i++) {
          validateDirectiveName(names[i]);
        }
      }
      if (Component.compilerOptions && isRuntimeOnly()) {
        warn$1(
          `"compilerOptions" is only supported when using a build of Vue that includes the runtime compiler. Since you are using a runtime-only build, the options should be passed via your build tool config instead.`
        );
      }
    }
    instance.accessCache = /* @__PURE__ */ Object.create(null);
    instance.proxy = new Proxy(instance.ctx, PublicInstanceProxyHandlers);
    if (true) {
      exposePropsOnRenderContext(instance);
    }
    const { setup } = Component;
    if (setup) {
      pauseTracking();
      const setupContext = instance.setupContext = setup.length > 1 ? createSetupContext(instance) : null;
      const reset = setCurrentInstance(instance);
      const setupResult = callWithErrorHandling(
        setup,
        instance,
        0,
        [
          true ? shallowReadonly(instance.props) : instance.props,
          setupContext
        ]
      );
      const isAsyncSetup = isPromise(setupResult);
      resetTracking();
      reset();
      if ((isAsyncSetup || instance.sp) && !isAsyncWrapper(instance)) {
        markAsyncBoundary(instance);
      }
      if (isAsyncSetup) {
        setupResult.then(unsetCurrentInstance, unsetCurrentInstance);
        if (isSSR) {
          return setupResult.then((resolvedResult) => {
            handleSetupResult(instance, resolvedResult, isSSR);
          }).catch((e) => {
            handleError(e, instance, 0);
          });
        } else {
          instance.asyncDep = setupResult;
          if (!instance.suspense) {
            const name = (_a = Component.name) != null ? _a : "Anonymous";
            warn$1(
              `Component <${name}>: setup function returned a promise, but no <Suspense> boundary was found in the parent component tree. A component with async setup() must be nested in a <Suspense> in order to be rendered.`
            );
          }
        }
      } else {
        handleSetupResult(instance, setupResult, isSSR);
      }
    } else {
      finishComponentSetup(instance, isSSR);
    }
  }
  function handleSetupResult(instance, setupResult, isSSR) {
    if (isFunction(setupResult)) {
      if (instance.type.__ssrInlineRender) {
        instance.ssrRender = setupResult;
      } else {
        instance.render = setupResult;
      }
    } else if (isObject(setupResult)) {
      if (isVNode(setupResult)) {
        warn$1(
          `setup() should not return VNodes directly - return a render function instead.`
        );
      }
      if (true) {
        instance.devtoolsRawSetupState = setupResult;
      }
      instance.setupState = proxyRefs(setupResult);
      if (true) {
        exposeSetupStateOnRenderContext(instance);
      }
    } else if (setupResult !== void 0) {
      warn$1(
        `setup() should return an object. Received: ${setupResult === null ? "null" : typeof setupResult}`
      );
    }
    finishComponentSetup(instance, isSSR);
  }
  var compile;
  var installWithProxy;
  var isRuntimeOnly = () => !compile;
  function finishComponentSetup(instance, isSSR, skipOptions) {
    const Component = instance.type;
    if (!instance.render) {
      if (!isSSR && compile && !Component.render) {
        const template = Component.template || resolveMergedOptions(instance).template;
        if (template) {
          if (true) {
            startMeasure(instance, `compile`);
          }
          const { isCustomElement, compilerOptions } = instance.appContext.config;
          const { delimiters, compilerOptions: componentCompilerOptions } = Component;
          const finalCompilerOptions = extend(
            extend(
              {
                isCustomElement,
                delimiters
              },
              compilerOptions
            ),
            componentCompilerOptions
          );
          Component.render = compile(template, finalCompilerOptions);
          if (true) {
            endMeasure(instance, `compile`);
          }
        }
      }
      instance.render = Component.render || NOOP;
      if (installWithProxy) {
        installWithProxy(instance);
      }
    }
    if (true) {
      const reset = setCurrentInstance(instance);
      pauseTracking();
      try {
        applyOptions(instance);
      } finally {
        resetTracking();
        reset();
      }
    }
    if (!Component.render && instance.render === NOOP && !isSSR) {
      if (!compile && Component.template) {
        warn$1(
          `Component provided template option but runtime compilation is not supported in this build of Vue. Configure your bundler to alias "vue" to "vue/dist/vue.esm-bundler.js".`
        );
      } else {
        warn$1(`Component is missing template or render function: `, Component);
      }
    }
  }
  var attrsProxyHandlers = true ? {
    get(target, key) {
      markAttrsAccessed();
      track(target, "get", "");
      return target[key];
    },
    set() {
      warn$1(`setupContext.attrs is readonly.`);
      return false;
    },
    deleteProperty() {
      warn$1(`setupContext.attrs is readonly.`);
      return false;
    }
  } : {
    get(target, key) {
      track(target, "get", "");
      return target[key];
    }
  };
  function getSlotsProxy(instance) {
    return new Proxy(instance.slots, {
      get(target, key) {
        track(instance, "get", "$slots");
        return target[key];
      }
    });
  }
  function createSetupContext(instance) {
    const expose = (exposed) => {
      if (true) {
        if (instance.exposed) {
          warn$1(`expose() should be called only once per setup().`);
        }
        if (exposed != null) {
          let exposedType = typeof exposed;
          if (exposedType === "object") {
            if (isArray(exposed)) {
              exposedType = "array";
            } else if (isRef2(exposed)) {
              exposedType = "ref";
            }
          }
          if (exposedType !== "object") {
            warn$1(
              `expose() should be passed a plain object, received ${exposedType}.`
            );
          }
        }
      }
      instance.exposed = exposed || {};
    };
    if (true) {
      let attrsProxy;
      let slotsProxy;
      return Object.freeze({
        get attrs() {
          return attrsProxy || (attrsProxy = new Proxy(instance.attrs, attrsProxyHandlers));
        },
        get slots() {
          return slotsProxy || (slotsProxy = getSlotsProxy(instance));
        },
        get emit() {
          return (event, ...args) => instance.emit(event, ...args);
        },
        expose
      });
    } else {
      return {
        attrs: new Proxy(instance.attrs, attrsProxyHandlers),
        slots: instance.slots,
        emit: instance.emit,
        expose
      };
    }
  }
  function getComponentPublicInstance(instance) {
    if (instance.exposed) {
      return instance.exposeProxy || (instance.exposeProxy = new Proxy(proxyRefs(markRaw(instance.exposed)), {
        get(target, key) {
          if (key in target) {
            return target[key];
          } else if (key in publicPropertiesMap) {
            return publicPropertiesMap[key](instance);
          }
        },
        has(target, key) {
          return key in target || key in publicPropertiesMap;
        }
      }));
    } else {
      return instance.proxy;
    }
  }
  var classifyRE = /(?:^|[-_])(\w)/g;
  var classify = (str) => str.replace(classifyRE, (c) => c.toUpperCase()).replace(/[-_]/g, "");
  function getComponentName(Component, includeInferred = true) {
    return isFunction(Component) ? Component.displayName || Component.name : Component.name || includeInferred && Component.__name;
  }
  function formatComponentName(instance, Component, isRoot = false) {
    let name = getComponentName(Component);
    if (!name && Component.__file) {
      const match = Component.__file.match(/([^/\\]+)\.\w+$/);
      if (match) {
        name = match[1];
      }
    }
    if (!name && instance && instance.parent) {
      const inferFromRegistry = (registry) => {
        for (const key in registry) {
          if (registry[key] === Component) {
            return key;
          }
        }
      };
      name = inferFromRegistry(
        instance.components || instance.parent.type.components
      ) || inferFromRegistry(instance.appContext.components);
    }
    return name ? classify(name) : isRoot ? `App` : `Anonymous`;
  }
  function isClassComponent(value) {
    return isFunction(value) && "__vccOpts" in value;
  }
  var computed2 = (getterOrOptions, debugOptions) => {
    const c = computed(getterOrOptions, debugOptions, isInSSRComponentSetup);
    if (true) {
      const i = getCurrentInstance();
      if (i && i.appContext.config.warnRecursiveComputed) {
        c._warnRecursive = true;
      }
    }
    return c;
  };
  function initCustomFormatter() {
    if (typeof window === "undefined") {
      return;
    }
    const vueStyle = { style: "color:#3ba776" };
    const numberStyle = { style: "color:#1677ff" };
    const stringStyle = { style: "color:#f5222d" };
    const keywordStyle = { style: "color:#eb2f96" };
    const formatter = {
      __vue_custom_formatter: true,
      header(obj) {
        if (!isObject(obj)) {
          return null;
        }
        if (obj.__isVue) {
          return ["div", vueStyle, `VueInstance`];
        } else if (isRef2(obj)) {
          return [
            "div",
            {},
            ["span", vueStyle, genRefFlag(obj)],
            "<",
            // avoid debugger accessing value affecting behavior
            formatValue("_value" in obj ? obj._value : obj),
            `>`
          ];
        } else if (isReactive(obj)) {
          return [
            "div",
            {},
            ["span", vueStyle, isShallow(obj) ? "ShallowReactive" : "Reactive"],
            "<",
            formatValue(obj),
            `>${isReadonly(obj) ? ` (readonly)` : ``}`
          ];
        } else if (isReadonly(obj)) {
          return [
            "div",
            {},
            ["span", vueStyle, isShallow(obj) ? "ShallowReadonly" : "Readonly"],
            "<",
            formatValue(obj),
            ">"
          ];
        }
        return null;
      },
      hasBody(obj) {
        return obj && obj.__isVue;
      },
      body(obj) {
        if (obj && obj.__isVue) {
          return [
            "div",
            {},
            ...formatInstance(obj.$)
          ];
        }
      }
    };
    function formatInstance(instance) {
      const blocks = [];
      if (instance.type.props && instance.props) {
        blocks.push(createInstanceBlock("props", toRaw(instance.props)));
      }
      if (instance.setupState !== EMPTY_OBJ) {
        blocks.push(createInstanceBlock("setup", instance.setupState));
      }
      if (instance.data !== EMPTY_OBJ) {
        blocks.push(createInstanceBlock("data", toRaw(instance.data)));
      }
      const computed3 = extractKeys(instance, "computed");
      if (computed3) {
        blocks.push(createInstanceBlock("computed", computed3));
      }
      const injected = extractKeys(instance, "inject");
      if (injected) {
        blocks.push(createInstanceBlock("injected", injected));
      }
      blocks.push([
        "div",
        {},
        [
          "span",
          {
            style: keywordStyle.style + ";opacity:0.66"
          },
          "$ (internal): "
        ],
        ["object", { object: instance }]
      ]);
      return blocks;
    }
    function createInstanceBlock(type, target) {
      target = extend({}, target);
      if (!Object.keys(target).length) {
        return ["span", {}];
      }
      return [
        "div",
        { style: "line-height:1.25em;margin-bottom:0.6em" },
        [
          "div",
          {
            style: "color:#476582"
          },
          type
        ],
        [
          "div",
          {
            style: "padding-left:1.25em"
          },
          ...Object.keys(target).map((key) => {
            return [
              "div",
              {},
              ["span", keywordStyle, key + ": "],
              formatValue(target[key], false)
            ];
          })
        ]
      ];
    }
    function formatValue(v, asRaw = true) {
      if (typeof v === "number") {
        return ["span", numberStyle, v];
      } else if (typeof v === "string") {
        return ["span", stringStyle, JSON.stringify(v)];
      } else if (typeof v === "boolean") {
        return ["span", keywordStyle, v];
      } else if (isObject(v)) {
        return ["object", { object: asRaw ? toRaw(v) : v }];
      } else {
        return ["span", stringStyle, String(v)];
      }
    }
    function extractKeys(instance, type) {
      const Comp = instance.type;
      if (isFunction(Comp)) {
        return;
      }
      const extracted = {};
      for (const key in instance.ctx) {
        if (isKeyOfType(Comp, key, type)) {
          extracted[key] = instance.ctx[key];
        }
      }
      return extracted;
    }
    function isKeyOfType(Comp, key, type) {
      const opts = Comp[type];
      if (isArray(opts) && opts.includes(key) || isObject(opts) && key in opts) {
        return true;
      }
      if (Comp.extends && isKeyOfType(Comp.extends, key, type)) {
        return true;
      }
      if (Comp.mixins && Comp.mixins.some((m) => isKeyOfType(m, key, type))) {
        return true;
      }
    }
    function genRefFlag(v) {
      if (isShallow(v)) {
        return `ShallowRef`;
      }
      if (v.effect) {
        return `ComputedRef`;
      }
      return `Ref`;
    }
    if (window.devtoolsFormatters) {
      window.devtoolsFormatters.push(formatter);
    } else {
      window.devtoolsFormatters = [formatter];
    }
  }
  var version = "3.5.13";
  var warn2 = true ? warn$1 : NOOP;

  // node_modules/@vue/runtime-dom/dist/runtime-dom.esm-bundler.js
  var policy = void 0;
  var tt = typeof window !== "undefined" && window.trustedTypes;
  if (tt) {
    try {
      policy = /* @__PURE__ */ tt.createPolicy("vue", {
        createHTML: (val) => val
      });
    } catch (e) {
      warn2(`Error creating trusted types policy: ${e}`);
    }
  }
  var unsafeToTrustedHTML = policy ? (val) => policy.createHTML(val) : (val) => val;
  var svgNS = "http://www.w3.org/2000/svg";
  var mathmlNS = "http://www.w3.org/1998/Math/MathML";
  var doc = typeof document !== "undefined" ? document : null;
  var templateContainer = doc && /* @__PURE__ */ doc.createElement("template");
  var nodeOps = {
    insert: (child, parent, anchor) => {
      parent.insertBefore(child, anchor || null);
    },
    remove: (child) => {
      const parent = child.parentNode;
      if (parent) {
        parent.removeChild(child);
      }
    },
    createElement: (tag, namespace, is, props) => {
      const el = namespace === "svg" ? doc.createElementNS(svgNS, tag) : namespace === "mathml" ? doc.createElementNS(mathmlNS, tag) : is ? doc.createElement(tag, { is }) : doc.createElement(tag);
      if (tag === "select" && props && props.multiple != null) {
        el.setAttribute("multiple", props.multiple);
      }
      return el;
    },
    createText: (text) => doc.createTextNode(text),
    createComment: (text) => doc.createComment(text),
    setText: (node, text) => {
      node.nodeValue = text;
    },
    setElementText: (el, text) => {
      el.textContent = text;
    },
    parentNode: (node) => node.parentNode,
    nextSibling: (node) => node.nextSibling,
    querySelector: (selector) => doc.querySelector(selector),
    setScopeId(el, id) {
      el.setAttribute(id, "");
    },
    // __UNSAFE__
    // Reason: innerHTML.
    // Static content here can only come from compiled templates.
    // As long as the user only uses trusted templates, this is safe.
    insertStaticContent(content, parent, anchor, namespace, start, end) {
      const before = anchor ? anchor.previousSibling : parent.lastChild;
      if (start && (start === end || start.nextSibling)) {
        while (true) {
          parent.insertBefore(start.cloneNode(true), anchor);
          if (start === end || !(start = start.nextSibling))
            break;
        }
      } else {
        templateContainer.innerHTML = unsafeToTrustedHTML(
          namespace === "svg" ? `<svg>${content}</svg>` : namespace === "mathml" ? `<math>${content}</math>` : content
        );
        const template = templateContainer.content;
        if (namespace === "svg" || namespace === "mathml") {
          const wrapper = template.firstChild;
          while (wrapper.firstChild) {
            template.appendChild(wrapper.firstChild);
          }
          template.removeChild(wrapper);
        }
        parent.insertBefore(template, anchor);
      }
      return [
        // first
        before ? before.nextSibling : parent.firstChild,
        // last
        anchor ? anchor.previousSibling : parent.lastChild
      ];
    }
  };
  var vtcKey = Symbol("_vtc");
  function patchClass(el, value, isSVG) {
    const transitionClasses = el[vtcKey];
    if (transitionClasses) {
      value = (value ? [value, ...transitionClasses] : [...transitionClasses]).join(" ");
    }
    if (value == null) {
      el.removeAttribute("class");
    } else if (isSVG) {
      el.setAttribute("class", value);
    } else {
      el.className = value;
    }
  }
  var vShowOriginalDisplay = Symbol("_vod");
  var vShowHidden = Symbol("_vsh");
  var vShow = {
    beforeMount(el, { value }, { transition }) {
      el[vShowOriginalDisplay] = el.style.display === "none" ? "" : el.style.display;
      if (transition && value) {
        transition.beforeEnter(el);
      } else {
        setDisplay(el, value);
      }
    },
    mounted(el, { value }, { transition }) {
      if (transition && value) {
        transition.enter(el);
      }
    },
    updated(el, { value, oldValue }, { transition }) {
      if (!value === !oldValue)
        return;
      if (transition) {
        if (value) {
          transition.beforeEnter(el);
          setDisplay(el, true);
          transition.enter(el);
        } else {
          transition.leave(el, () => {
            setDisplay(el, false);
          });
        }
      } else {
        setDisplay(el, value);
      }
    },
    beforeUnmount(el, { value }) {
      setDisplay(el, value);
    }
  };
  if (true) {
    vShow.name = "show";
  }
  function setDisplay(el, value) {
    el.style.display = value ? el[vShowOriginalDisplay] : "none";
    el[vShowHidden] = !value;
  }
  var CSS_VAR_TEXT = Symbol(true ? "CSS_VAR_TEXT" : "");
  var displayRE = /(^|;)\s*display\s*:/;
  function patchStyle(el, prev, next) {
    const style = el.style;
    const isCssString = isString(next);
    let hasControlledDisplay = false;
    if (next && !isCssString) {
      if (prev) {
        if (!isString(prev)) {
          for (const key in prev) {
            if (next[key] == null) {
              setStyle(style, key, "");
            }
          }
        } else {
          for (const prevStyle of prev.split(";")) {
            const key = prevStyle.slice(0, prevStyle.indexOf(":")).trim();
            if (next[key] == null) {
              setStyle(style, key, "");
            }
          }
        }
      }
      for (const key in next) {
        if (key === "display") {
          hasControlledDisplay = true;
        }
        setStyle(style, key, next[key]);
      }
    } else {
      if (isCssString) {
        if (prev !== next) {
          const cssVarText = style[CSS_VAR_TEXT];
          if (cssVarText) {
            next += ";" + cssVarText;
          }
          style.cssText = next;
          hasControlledDisplay = displayRE.test(next);
        }
      } else if (prev) {
        el.removeAttribute("style");
      }
    }
    if (vShowOriginalDisplay in el) {
      el[vShowOriginalDisplay] = hasControlledDisplay ? style.display : "";
      if (el[vShowHidden]) {
        style.display = "none";
      }
    }
  }
  var semicolonRE = /[^\\];\s*$/;
  var importantRE = /\s*!important$/;
  function setStyle(style, name, val) {
    if (isArray(val)) {
      val.forEach((v) => setStyle(style, name, v));
    } else {
      if (val == null)
        val = "";
      if (true) {
        if (semicolonRE.test(val)) {
          warn2(
            `Unexpected semicolon at the end of '${name}' style value: '${val}'`
          );
        }
      }
      if (name.startsWith("--")) {
        style.setProperty(name, val);
      } else {
        const prefixed = autoPrefix(style, name);
        if (importantRE.test(val)) {
          style.setProperty(
            hyphenate(prefixed),
            val.replace(importantRE, ""),
            "important"
          );
        } else {
          style[prefixed] = val;
        }
      }
    }
  }
  var prefixes = ["Webkit", "Moz", "ms"];
  var prefixCache = {};
  function autoPrefix(style, rawName) {
    const cached = prefixCache[rawName];
    if (cached) {
      return cached;
    }
    let name = camelize(rawName);
    if (name !== "filter" && name in style) {
      return prefixCache[rawName] = name;
    }
    name = capitalize(name);
    for (let i = 0; i < prefixes.length; i++) {
      const prefixed = prefixes[i] + name;
      if (prefixed in style) {
        return prefixCache[rawName] = prefixed;
      }
    }
    return rawName;
  }
  var xlinkNS = "http://www.w3.org/1999/xlink";
  function patchAttr(el, key, value, isSVG, instance, isBoolean2 = isSpecialBooleanAttr(key)) {
    if (isSVG && key.startsWith("xlink:")) {
      if (value == null) {
        el.removeAttributeNS(xlinkNS, key.slice(6, key.length));
      } else {
        el.setAttributeNS(xlinkNS, key, value);
      }
    } else {
      if (value == null || isBoolean2 && !includeBooleanAttr(value)) {
        el.removeAttribute(key);
      } else {
        el.setAttribute(
          key,
          isBoolean2 ? "" : isSymbol(value) ? String(value) : value
        );
      }
    }
  }
  function patchDOMProp(el, key, value, parentComponent, attrName) {
    if (key === "innerHTML" || key === "textContent") {
      if (value != null) {
        el[key] = key === "innerHTML" ? unsafeToTrustedHTML(value) : value;
      }
      return;
    }
    const tag = el.tagName;
    if (key === "value" && tag !== "PROGRESS" && // custom elements may use _value internally
    !tag.includes("-")) {
      const oldValue = tag === "OPTION" ? el.getAttribute("value") || "" : el.value;
      const newValue = value == null ? (
        // #11647: value should be set as empty string for null and undefined,
        // but <input type="checkbox"> should be set as 'on'.
        el.type === "checkbox" ? "on" : ""
      ) : String(value);
      if (oldValue !== newValue || !("_value" in el)) {
        el.value = newValue;
      }
      if (value == null) {
        el.removeAttribute(key);
      }
      el._value = value;
      return;
    }
    let needRemove = false;
    if (value === "" || value == null) {
      const type = typeof el[key];
      if (type === "boolean") {
        value = includeBooleanAttr(value);
      } else if (value == null && type === "string") {
        value = "";
        needRemove = true;
      } else if (type === "number") {
        value = 0;
        needRemove = true;
      }
    }
    try {
      el[key] = value;
    } catch (e) {
      if (!needRemove) {
        warn2(
          `Failed setting prop "${key}" on <${tag.toLowerCase()}>: value ${value} is invalid.`,
          e
        );
      }
    }
    needRemove && el.removeAttribute(attrName || key);
  }
  function addEventListener(el, event, handler, options) {
    el.addEventListener(event, handler, options);
  }
  function removeEventListener(el, event, handler, options) {
    el.removeEventListener(event, handler, options);
  }
  var veiKey = Symbol("_vei");
  function patchEvent(el, rawName, prevValue, nextValue, instance = null) {
    const invokers = el[veiKey] || (el[veiKey] = {});
    const existingInvoker = invokers[rawName];
    if (nextValue && existingInvoker) {
      existingInvoker.value = true ? sanitizeEventValue(nextValue, rawName) : nextValue;
    } else {
      const [name, options] = parseName(rawName);
      if (nextValue) {
        const invoker = invokers[rawName] = createInvoker(
          true ? sanitizeEventValue(nextValue, rawName) : nextValue,
          instance
        );
        addEventListener(el, name, invoker, options);
      } else if (existingInvoker) {
        removeEventListener(el, name, existingInvoker, options);
        invokers[rawName] = void 0;
      }
    }
  }
  var optionsModifierRE = /(?:Once|Passive|Capture)$/;
  function parseName(name) {
    let options;
    if (optionsModifierRE.test(name)) {
      options = {};
      let m;
      while (m = name.match(optionsModifierRE)) {
        name = name.slice(0, name.length - m[0].length);
        options[m[0].toLowerCase()] = true;
      }
    }
    const event = name[2] === ":" ? name.slice(3) : hyphenate(name.slice(2));
    return [event, options];
  }
  var cachedNow = 0;
  var p = /* @__PURE__ */ Promise.resolve();
  var getNow = () => cachedNow || (p.then(() => cachedNow = 0), cachedNow = Date.now());
  function createInvoker(initialValue, instance) {
    const invoker = (e) => {
      if (!e._vts) {
        e._vts = Date.now();
      } else if (e._vts <= invoker.attached) {
        return;
      }
      callWithAsyncErrorHandling(
        patchStopImmediatePropagation(e, invoker.value),
        instance,
        5,
        [e]
      );
    };
    invoker.value = initialValue;
    invoker.attached = getNow();
    return invoker;
  }
  function sanitizeEventValue(value, propName) {
    if (isFunction(value) || isArray(value)) {
      return value;
    }
    warn2(
      `Wrong type passed as event handler to ${propName} - did you forget @ or : in front of your prop?
Expected function or array of functions, received type ${typeof value}.`
    );
    return NOOP;
  }
  function patchStopImmediatePropagation(e, value) {
    if (isArray(value)) {
      const originalStop = e.stopImmediatePropagation;
      e.stopImmediatePropagation = () => {
        originalStop.call(e);
        e._stopped = true;
      };
      return value.map(
        (fn) => (e2) => !e2._stopped && fn && fn(e2)
      );
    } else {
      return value;
    }
  }
  var isNativeOn = (key) => key.charCodeAt(0) === 111 && key.charCodeAt(1) === 110 && // lowercase letter
  key.charCodeAt(2) > 96 && key.charCodeAt(2) < 123;
  var patchProp = (el, key, prevValue, nextValue, namespace, parentComponent) => {
    const isSVG = namespace === "svg";
    if (key === "class") {
      patchClass(el, nextValue, isSVG);
    } else if (key === "style") {
      patchStyle(el, prevValue, nextValue);
    } else if (isOn(key)) {
      if (!isModelListener(key)) {
        patchEvent(el, key, prevValue, nextValue, parentComponent);
      }
    } else if (key[0] === "." ? (key = key.slice(1), true) : key[0] === "^" ? (key = key.slice(1), false) : shouldSetAsProp(el, key, nextValue, isSVG)) {
      patchDOMProp(el, key, nextValue);
      if (!el.tagName.includes("-") && (key === "value" || key === "checked" || key === "selected")) {
        patchAttr(el, key, nextValue, isSVG, parentComponent, key !== "value");
      }
    } else if (
      // #11081 force set props for possible async custom element
      el._isVueCE && (/[A-Z]/.test(key) || !isString(nextValue))
    ) {
      patchDOMProp(el, camelize(key), nextValue, parentComponent, key);
    } else {
      if (key === "true-value") {
        el._trueValue = nextValue;
      } else if (key === "false-value") {
        el._falseValue = nextValue;
      }
      patchAttr(el, key, nextValue, isSVG);
    }
  };
  function shouldSetAsProp(el, key, value, isSVG) {
    if (isSVG) {
      if (key === "innerHTML" || key === "textContent") {
        return true;
      }
      if (key in el && isNativeOn(key) && isFunction(value)) {
        return true;
      }
      return false;
    }
    if (key === "spellcheck" || key === "draggable" || key === "translate") {
      return false;
    }
    if (key === "form") {
      return false;
    }
    if (key === "list" && el.tagName === "INPUT") {
      return false;
    }
    if (key === "type" && el.tagName === "TEXTAREA") {
      return false;
    }
    if (key === "width" || key === "height") {
      const tag = el.tagName;
      if (tag === "IMG" || tag === "VIDEO" || tag === "CANVAS" || tag === "SOURCE") {
        return false;
      }
    }
    if (isNativeOn(key) && isString(value)) {
      return false;
    }
    return key in el;
  }
  var moveCbKey = Symbol("_moveCb");
  var enterCbKey2 = Symbol("_enterCb");
  var getModelAssigner = (vnode) => {
    const fn = vnode.props["onUpdate:modelValue"] || false;
    return isArray(fn) ? (value) => invokeArrayFns(fn, value) : fn;
  };
  function onCompositionStart(e) {
    e.target.composing = true;
  }
  function onCompositionEnd(e) {
    const target = e.target;
    if (target.composing) {
      target.composing = false;
      target.dispatchEvent(new Event("input"));
    }
  }
  var assignKey = Symbol("_assign");
  var vModelText = {
    created(el, { modifiers: { lazy, trim, number } }, vnode) {
      el[assignKey] = getModelAssigner(vnode);
      const castToNumber = number || vnode.props && vnode.props.type === "number";
      addEventListener(el, lazy ? "change" : "input", (e) => {
        if (e.target.composing)
          return;
        let domValue = el.value;
        if (trim) {
          domValue = domValue.trim();
        }
        if (castToNumber) {
          domValue = looseToNumber(domValue);
        }
        el[assignKey](domValue);
      });
      if (trim) {
        addEventListener(el, "change", () => {
          el.value = el.value.trim();
        });
      }
      if (!lazy) {
        addEventListener(el, "compositionstart", onCompositionStart);
        addEventListener(el, "compositionend", onCompositionEnd);
        addEventListener(el, "change", onCompositionEnd);
      }
    },
    // set value on mounted so it's after min/max for type="range"
    mounted(el, { value }) {
      el.value = value == null ? "" : value;
    },
    beforeUpdate(el, { value, oldValue, modifiers: { lazy, trim, number } }, vnode) {
      el[assignKey] = getModelAssigner(vnode);
      if (el.composing)
        return;
      const elValue = (number || el.type === "number") && !/^0\d/.test(el.value) ? looseToNumber(el.value) : el.value;
      const newValue = value == null ? "" : value;
      if (elValue === newValue) {
        return;
      }
      if (document.activeElement === el && el.type !== "range") {
        if (lazy && value === oldValue) {
          return;
        }
        if (trim && el.value.trim() === newValue) {
          return;
        }
      }
      el.value = newValue;
    }
  };
  var vModelCheckbox = {
    // #4096 array checkboxes need to be deep traversed
    deep: true,
    created(el, _, vnode) {
      el[assignKey] = getModelAssigner(vnode);
      addEventListener(el, "change", () => {
        const modelValue = el._modelValue;
        const elementValue = getValue(el);
        const checked = el.checked;
        const assign = el[assignKey];
        if (isArray(modelValue)) {
          const index = looseIndexOf(modelValue, elementValue);
          const found = index !== -1;
          if (checked && !found) {
            assign(modelValue.concat(elementValue));
          } else if (!checked && found) {
            const filtered = [...modelValue];
            filtered.splice(index, 1);
            assign(filtered);
          }
        } else if (isSet(modelValue)) {
          const cloned = new Set(modelValue);
          if (checked) {
            cloned.add(elementValue);
          } else {
            cloned.delete(elementValue);
          }
          assign(cloned);
        } else {
          assign(getCheckboxValue(el, checked));
        }
      });
    },
    // set initial checked on mount to wait for true-value/false-value
    mounted: setChecked,
    beforeUpdate(el, binding, vnode) {
      el[assignKey] = getModelAssigner(vnode);
      setChecked(el, binding, vnode);
    }
  };
  function setChecked(el, { value, oldValue }, vnode) {
    el._modelValue = value;
    let checked;
    if (isArray(value)) {
      checked = looseIndexOf(value, vnode.props.value) > -1;
    } else if (isSet(value)) {
      checked = value.has(vnode.props.value);
    } else {
      if (value === oldValue)
        return;
      checked = looseEqual(value, getCheckboxValue(el, true));
    }
    if (el.checked !== checked) {
      el.checked = checked;
    }
  }
  var vModelSelect = {
    // <select multiple> value need to be deep traversed
    deep: true,
    created(el, { value, modifiers: { number } }, vnode) {
      const isSetModel = isSet(value);
      addEventListener(el, "change", () => {
        const selectedVal = Array.prototype.filter.call(el.options, (o) => o.selected).map(
          (o) => number ? looseToNumber(getValue(o)) : getValue(o)
        );
        el[assignKey](
          el.multiple ? isSetModel ? new Set(selectedVal) : selectedVal : selectedVal[0]
        );
        el._assigning = true;
        nextTick(() => {
          el._assigning = false;
        });
      });
      el[assignKey] = getModelAssigner(vnode);
    },
    // set value in mounted & updated because <select> relies on its children
    // <option>s.
    mounted(el, { value }) {
      setSelected(el, value);
    },
    beforeUpdate(el, _binding, vnode) {
      el[assignKey] = getModelAssigner(vnode);
    },
    updated(el, { value }) {
      if (!el._assigning) {
        setSelected(el, value);
      }
    }
  };
  function setSelected(el, value) {
    const isMultiple = el.multiple;
    const isArrayValue = isArray(value);
    if (isMultiple && !isArrayValue && !isSet(value)) {
      warn2(
        `<select multiple v-model> expects an Array or Set value for its binding, but got ${Object.prototype.toString.call(value).slice(8, -1)}.`
      );
      return;
    }
    for (let i = 0, l = el.options.length; i < l; i++) {
      const option = el.options[i];
      const optionValue = getValue(option);
      if (isMultiple) {
        if (isArrayValue) {
          const optionType = typeof optionValue;
          if (optionType === "string" || optionType === "number") {
            option.selected = value.some((v) => String(v) === String(optionValue));
          } else {
            option.selected = looseIndexOf(value, optionValue) > -1;
          }
        } else {
          option.selected = value.has(optionValue);
        }
      } else if (looseEqual(getValue(option), value)) {
        if (el.selectedIndex !== i)
          el.selectedIndex = i;
        return;
      }
    }
    if (!isMultiple && el.selectedIndex !== -1) {
      el.selectedIndex = -1;
    }
  }
  function getValue(el) {
    return "_value" in el ? el._value : el.value;
  }
  function getCheckboxValue(el, checked) {
    const key = checked ? "_trueValue" : "_falseValue";
    return key in el ? el[key] : checked;
  }
  var rendererOptions = /* @__PURE__ */ extend({ patchProp }, nodeOps);
  var renderer;
  function ensureRenderer() {
    return renderer || (renderer = createRenderer(rendererOptions));
  }
  var createApp = (...args) => {
    const app2 = ensureRenderer().createApp(...args);
    if (true) {
      injectNativeTagCheck(app2);
      injectCompilerOptionsCheck(app2);
    }
    const { mount } = app2;
    app2.mount = (containerOrSelector) => {
      const container = normalizeContainer(containerOrSelector);
      if (!container)
        return;
      const component = app2._component;
      if (!isFunction(component) && !component.render && !component.template) {
        component.template = container.innerHTML;
      }
      if (container.nodeType === 1) {
        container.textContent = "";
      }
      const proxy = mount(container, false, resolveRootNamespace(container));
      if (container instanceof Element) {
        container.removeAttribute("v-cloak");
        container.setAttribute("data-v-app", "");
      }
      return proxy;
    };
    return app2;
  };
  function resolveRootNamespace(container) {
    if (container instanceof SVGElement) {
      return "svg";
    }
    if (typeof MathMLElement === "function" && container instanceof MathMLElement) {
      return "mathml";
    }
  }
  function injectNativeTagCheck(app2) {
    Object.defineProperty(app2.config, "isNativeTag", {
      value: (tag) => isHTMLTag(tag) || isSVGTag(tag) || isMathMLTag(tag),
      writable: false
    });
  }
  function injectCompilerOptionsCheck(app2) {
    if (isRuntimeOnly()) {
      const isCustomElement = app2.config.isCustomElement;
      Object.defineProperty(app2.config, "isCustomElement", {
        get() {
          return isCustomElement;
        },
        set() {
          warn2(
            `The \`isCustomElement\` config option is deprecated. Use \`compilerOptions.isCustomElement\` instead.`
          );
        }
      });
      const compilerOptions = app2.config.compilerOptions;
      const msg = `The \`compilerOptions\` config option is only respected when using a build of Vue.js that includes the runtime compiler (aka "full build"). Since you are using the runtime-only build, \`compilerOptions\` must be passed to \`@vue/compiler-dom\` in the build setup instead.
- For vue-loader: pass it via vue-loader's \`compilerOptions\` loader option.
- For vue-cli: see https://cli.vuejs.org/guide/webpack.html#modifying-options-of-a-loader
- For vite: pass it via @vitejs/plugin-vue options. See https://github.com/vitejs/vite-plugin-vue/tree/main/packages/plugin-vue#example-for-passing-options-to-vuecompiler-sfc`;
      Object.defineProperty(app2.config, "compilerOptions", {
        get() {
          warn2(msg);
          return compilerOptions;
        },
        set() {
          warn2(msg);
        }
      });
    }
  }
  function normalizeContainer(container) {
    if (isString(container)) {
      const res = document.querySelector(container);
      if (!res) {
        warn2(
          `Failed to mount app: mount target selector "${container}" returned null.`
        );
      }
      return res;
    }
    if (window.ShadowRoot && container instanceof window.ShadowRoot && container.mode === "closed") {
      warn2(
        `mounting on a ShadowRoot with \`{mode: "closed"}\` may lead to unpredictable bugs`
      );
    }
    return container;
  }

  // node_modules/vue/dist/vue.runtime.esm-bundler.js
  function initDev() {
    {
      initCustomFormatter();
    }
  }
  if (true) {
    initDev();
  }

  // sfc-script:/home/bjoern/development/onto-spread-ed/js/release/ProgressIndicator.vue?type=script
  var ProgressIndicator_default = /* @__PURE__ */ defineComponent({
    __name: "ProgressIndicator",
    props: {
      release: { type: null, required: false },
      details: { type: Object, required: false }
    },
    setup(__props, { expose: __expose }) {
      __expose();
      const props = __props;
      const percent = computed2(() => Math.round((props.details?.__progress?.progress ?? 0) * 100));
      const __returned__ = { props, percent };
      Object.defineProperty(__returned__, "__isScriptSetup", { enumerable: false, value: true });
      return __returned__;
    }
  });

  // sfc-template:/home/bjoern/development/onto-spread-ed/js/release/ProgressIndicator.vue?type=template
  var _hoisted_1 = { class: "text-secondary mb-3" };
  var _hoisted_2 = {
    class: "progress",
    role: "progressbar"
  };
  var _hoisted_3 = {
    key: 1,
    class: "d-flex justify-content-center mt-5"
  };
  function render(_ctx, _cache, $props, $setup, $data, $options) {
    return $props.release?.state == "running" ? (openBlock(), createElementBlock(
      Fragment,
      { key: 0 },
      [
        createBaseVNode("p", null, [
          renderSlot(_ctx.$slots, "default")
        ]),
        $props.details && "__progress" in $props.details && $props.details?.__progress ? (openBlock(), createElementBlock(
          Fragment,
          { key: 0 },
          [
            createBaseVNode(
              "p",
              _hoisted_1,
              toDisplayString($props.details.__progress.message ?? "Working on") + " " + toDisplayString($props.details.__progress.current_item) + " (" + toDisplayString($props.details.__progress.position[0]) + "/" + toDisplayString($props.details.__progress.position[1]) + ") ",
              1
              /* TEXT */
            ),
            createBaseVNode("div", _hoisted_2, [
              createBaseVNode(
                "div",
                {
                  class: "progress-bar progress-bar-striped progress-bar-animated",
                  style: normalizeStyle({ width: `${$setup.percent}%` })
                },
                toDisplayString($setup.percent) + "% ",
                5
                /* TEXT, STYLE */
              )
            ])
          ],
          64
          /* STABLE_FRAGMENT */
        )) : (openBlock(), createElementBlock("div", _hoisted_3, _cache[0] || (_cache[0] = [
          createBaseVNode(
            "div",
            {
              class: "spinner-border text-primary",
              role: "status",
              style: { "width": "5rem", "height": "5rem" }
            },
            [
              createBaseVNode("span", { class: "visually-hidden" }, "Waiting...")
            ],
            -1
            /* HOISTED */
          )
        ])))
      ],
      64
      /* STABLE_FRAGMENT */
    )) : createCommentVNode("v-if", true);
  }

  // js/release/ProgressIndicator.vue
  ProgressIndicator_default.render = render;
  ProgressIndicator_default.__file = "js/release/ProgressIndicator.vue";
  var ProgressIndicator_default2 = ProgressIndicator_default;

  // sfc-script:/home/bjoern/development/onto-spread-ed/js/release/steps/AddictOVocab.vue?type=script
  var AddictOVocab_default = /* @__PURE__ */ defineComponent({
    __name: "AddictOVocab",
    props: {
      data: { type: null, required: true },
      release: { type: null, required: true },
      selectedSubStep: { type: [String, null], required: true }
    },
    emits: ["release-control"],
    setup(__props, { expose: __expose }) {
      __expose();
      const __returned__ = { ProgressIndicator: ProgressIndicator_default2 };
      Object.defineProperty(__returned__, "__isScriptSetup", { enumerable: false, value: true });
      return __returned__;
    }
  });

  // sfc-template:/home/bjoern/development/onto-spread-ed/js/release/steps/AddictOVocab.vue?type=template
  var _hoisted_12 = { class: "alert alert-danger" };
  var _hoisted_22 = { key: 1 };
  var _hoisted_32 = { key: 2 };
  function render2(_ctx, _cache, $props, $setup, $data, $options) {
    return openBlock(), createElementBlock(
      Fragment,
      null,
      [
        _cache[1] || (_cache[1] = createBaseVNode(
          "h3",
          null,
          "Publishing the release",
          -1
          /* HOISTED */
        )),
        $props.release.state === "waiting-for-user" && $props.data?.errors?.length > 0 ? (openBlock(true), createElementBlock(
          Fragment,
          { key: 0 },
          renderList($props.data.errors, (error) => {
            return openBlock(), createElementBlock("div", _hoisted_12, [
              error.details && error?.response?.["hydra:description"] ? (openBlock(), createElementBlock(
                Fragment,
                { key: 0 },
                [
                  createBaseVNode(
                    "h4",
                    null,
                    toDisplayString(error.response["hydra:title"]),
                    1
                    /* TEXT */
                  ),
                  createBaseVNode(
                    "p",
                    null,
                    toDisplayString(error.details),
                    1
                    /* TEXT */
                  ),
                  createBaseVNode(
                    "p",
                    null,
                    toDisplayString(error.response["hydra:description"]),
                    1
                    /* TEXT */
                  )
                ],
                64
                /* STABLE_FRAGMENT */
              )) : (openBlock(), createElementBlock(
                "pre",
                _hoisted_22,
                toDisplayString(JSON.stringify(error, void 0, 2)),
                1
                /* TEXT */
              ))
            ]);
          }),
          256
          /* UNKEYED_FRAGMENT */
        )) : (openBlock(), createBlock($setup["ProgressIndicator"], {
          key: 1,
          details: $props.data,
          release: $props.release
        }, {
          default: withCtx(() => _cache[0] || (_cache[0] = [
            createBaseVNode(
              "p",
              null,
              [
                createTextVNode(" The ontologies are being published to AddictOVocab. This will take a while."),
                createBaseVNode("br")
              ],
              -1
              /* HOISTED */
            )
          ])),
          _: 1
          /* STABLE */
        }, 8, ["details", "release"])),
        $props.release.state === "completed" ? (openBlock(), createElementBlock("p", _hoisted_32, " The ontologies were published to AddictOVocab. ")) : createCommentVNode("v-if", true)
      ],
      64
      /* STABLE_FRAGMENT */
    );
  }

  // js/release/steps/AddictOVocab.vue
  AddictOVocab_default.render = render2;
  AddictOVocab_default.__file = "js/release/steps/AddictOVocab.vue";
  var AddictOVocab_default2 = AddictOVocab_default;

  // sfc-script:/home/bjoern/development/onto-spread-ed/js/common/CollapsibleCard.vue?type=script
  var CollapsibleCard_default = /* @__PURE__ */ defineComponent({
    __name: "CollapsibleCard",
    setup(__props, { expose: __expose }) {
      __expose();
      const body = ref(null);
      let id = Math.round(Math.random() * 1e4);
      const __returned__ = { body, get id() {
        return id;
      }, set id(v) {
        id = v;
      } };
      Object.defineProperty(__returned__, "__isScriptSetup", { enumerable: false, value: true });
      return __returned__;
    }
  });

  // sfc-style:/home/bjoern/development/onto-spread-ed/js/common/CollapsibleCard.vue?type=style&index=0
  {
    const el = document.createElement("style");
    el.textContent = ".collapsible-card[data-v-17ce3acb] {\n  border-width: 2px 2px 4px 2px;\n  border-style: solid;\n  border-color: #DDDDDD;\n  border-radius: 4px;\n}\n.collapsible-card .header[data-v-17ce3acb] {\n  padding: 14px 20px 14px 14px;\n  display: flex;\n  gap: 14px;\n  cursor: pointer;\n  border-bottom: 2px solid #DDDDDD;\n}\n.collapsible-card .header .title[data-v-17ce3acb] {\n  font-size: large;\n}\n.collapsible-card .header span[data-v-17ce3acb] {\n  flex-grow: 1;\n}\n.collapsible-card .header i[data-v-17ce3acb] {\n  align-self: center;\n  transition: transform 1s;\n}\n.collapsible-card .header.collapsed[data-v-17ce3acb] {\n  transition: border-bottom-width;\n  border-bottom-width: 0;\n  transition-delay: 1s;\n}\n.collapsible-card .header.collapsed i[data-v-17ce3acb] {\n  transform: rotate(180deg);\n}\n.collapsible-card .body[data-v-17ce3acb] {\n  margin: 14px 20px 14px 14px;\n  transition: height 1s;\n  box-sizing: border-box;\n}";
    document.head.append(el);
  }

  // sfc-template:/home/bjoern/development/onto-spread-ed/js/common/CollapsibleCard.vue?type=template
  var _hoisted_13 = { class: "collapsible-card" };
  var _hoisted_23 = ["data-bs-target"];
  var _hoisted_33 = { class: "title" };
  var _hoisted_4 = ["id"];
  function render3(_ctx, _cache, $props, $setup, $data, $options) {
    return openBlock(), createElementBlock("div", _hoisted_13, [
      createBaseVNode("div", {
        class: "header collapsed",
        "data-bs-toggle": "collapse",
        "data-bs-target": "#body-" + $setup.id
      }, [
        createBaseVNode("div", _hoisted_33, [
          renderSlot(_ctx.$slots, "title", {}, void 0, true)
        ]),
        _cache[0] || (_cache[0] = createBaseVNode(
          "span",
          null,
          null,
          -1
          /* HOISTED */
        )),
        renderSlot(_ctx.$slots, "buttons", {}, void 0, true),
        _cache[1] || (_cache[1] = createBaseVNode(
          "i",
          { class: "fa fa-chevron-up" },
          null,
          -1
          /* HOISTED */
        ))
      ], 8, _hoisted_23),
      createBaseVNode("div", {
        class: "body collapse",
        id: "body-" + $setup.id,
        ref: "body"
      }, [
        renderSlot(_ctx.$slots, "body", {}, void 0, true)
      ], 8, _hoisted_4)
    ]);
  }

  // js/common/CollapsibleCard.vue
  CollapsibleCard_default.render = render3;
  CollapsibleCard_default.__file = "js/common/CollapsibleCard.vue";
  CollapsibleCard_default.__scopeId = "data-v-17ce3acb";
  var CollapsibleCard_default2 = CollapsibleCard_default;

  // sfc-script:/home/bjoern/development/onto-spread-ed/js/release/ReleaseScriptViewer.vue?type=script
  var ReleaseScriptViewer_default = /* @__PURE__ */ defineComponent({
    __name: "ReleaseScriptViewer",
    props: {
      releaseScript: { type: null, required: true }
    },
    setup(__props, { expose: __expose }) {
      __expose();
      const props = __props;
      function setAnnotations(name, annotations) {
        props.releaseScript.files[name].target.ontology_annotations = Object.fromEntries(annotations.split("\n").map((l) => l.split(": ")));
      }
      function setArgs(step, args) {
        props.releaseScript.steps[step].args = Object.fromEntries(args.split("\n").map((l) => l.split(": ")));
      }
      function addDependency(name) {
        bootbox.prompt({
          title: `Add dependency for ${name}`,
          inputType: "select",
          inputOptions: Object.entries(props.releaseScript.files).filter(([k, _]) => k != name).map(([k, v]) => ({
            text: v.target.file,
            value: k
          })),
          callback(value) {
            if (value) {
              props.releaseScript.files[name].needs.push(value);
            }
          }
        });
      }
      function deleteDependency(name, dependency) {
        props.releaseScript.files[name].needs = props.releaseScript.files[name].needs.filter((x) => x != dependency);
      }
      function addFile() {
        bootbox.prompt({
          title: `What is the name of the file?`,
          inputType: "text",
          callback(value) {
            if (value) {
              value = value.trim().replace(/[ ,./\-!?=]/, "_");
              props.releaseScript.files[value] = {
                target: {
                  file: "",
                  iri: "",
                  ontology_annotations: {}
                },
                sources: [],
                needs: []
              };
            }
          }
        });
      }
      function renameFile(event, name) {
        event.preventDefault();
        bootbox.prompt({
          title: `What is the name of the file?`,
          inputType: "text",
          value: name,
          callback(value) {
            if (value) {
              value = value.trim().replace(/[ ,./\-!?=]/, "_");
              props.releaseScript.files[value] = props.releaseScript.files[name];
              delete props.releaseScript.files[name];
            }
          }
        });
      }
      function addStep(event, before) {
        event.preventDefault();
        props.releaseScript.steps.splice(before, 0, { args: {}, name: "NEW_STEP" });
      }
      function deleteStep(event, index) {
        event.preventDefault();
        const step = props.releaseScript.steps[index];
        bootbox.confirm({
          title: `Delete step '${step.name}'`,
          message: `Do you want to remove the release step '${step.name}'?`,
          buttons: {
            confirm: {
              label: `Delete ${step.name}`,
              className: "btn-danger"
            },
            cancel: {
              label: "Keep it",
              className: "btn-success"
            }
          },
          callback(result) {
            if (result) {
              props.releaseScript.steps.splice(index, 1);
            }
          }
        });
      }
      function deleteFile(event, name) {
        event.preventDefault();
        bootbox.confirm({
          title: `Delete '${name}'`,
          message: `Do you want to delete the file '${name}'? It will remove the file ${props.releaseScript.files[name].target.file} from the release.`,
          buttons: {
            confirm: {
              label: `Delete ${name}`,
              className: "btn-danger"
            },
            cancel: {
              label: "Keep it",
              className: "btn-success"
            }
          },
          callback(result) {
            if (result) {
              delete props.releaseScript.files[name];
            }
          }
        });
      }
      const __returned__ = { props, setAnnotations, setArgs, addDependency, deleteDependency, addFile, renameFile, addStep, deleteStep, deleteFile, CollapsibleCard: CollapsibleCard_default2 };
      Object.defineProperty(__returned__, "__isScriptSetup", { enumerable: false, value: true });
      return __returned__;
    }
  });

  // sfc-style:/home/bjoern/development/onto-spread-ed/js/release/ReleaseScriptViewer.vue?type=style&index=0
  {
    const el = document.createElement("style");
    el.textContent = ".release-file-settings[data-v-033a957d] {\n  display: grid;\n  grid-template-columns: 1fr auto;\n  grid-gap: 0 16px;\n}\n.release-file-settings > h6[data-v-033a957d], .release-file-settings > p[data-v-033a957d] {\n  grid-column: 1/3;\n}\n.release-file-settings > .input-group[data-v-033a957d] {\n  grid-column: 1;\n}\n.release-file-settings > label[data-v-033a957d] {\n  grid-column: 1;\n}\n.release-file-settings > .btn[data-v-033a957d] {\n  width: fit-content;\n  justify-self: start;\n  grid-column: 1;\n}\n.files[data-v-033a957d] {\n  display: flex;\n  flex-direction: column;\n  gap: 14px;\n}\n.btn.add-file[data-v-033a957d] {\n  width: fit-content;\n}\n.header[data-v-033a957d] {\n  display: flex;\n  gap: 14px;\n}\n.header .title[data-v-033a957d] {\n  font-size: large;\n}\n.header span[data-v-033a957d] {\n  flex-grow: 1;\n}\n.header i[data-v-033a957d] {\n  align-self: center;\n  transition: transform 1s;\n}\n.btn.add-step[data-v-033a957d] {\n  width: 100%;\n  border-style: dashed;\n}";
    document.head.append(el);
  }

  // sfc-template:/home/bjoern/development/onto-spread-ed/js/release/ReleaseScriptViewer.vue?type=template
  var _hoisted_14 = { class: "files" };
  var _hoisted_24 = { class: "badge text-bg-secondary" };
  var _hoisted_34 = {
    key: 0,
    class: "badge text-bg-secondary ms-1"
  };
  var _hoisted_42 = ["onClick"];
  var _hoisted_5 = ["onClick"];
  var _hoisted_6 = { class: "release-file-settings" };
  var _hoisted_7 = { class: "form-check form-switch mb-3" };
  var _hoisted_8 = ["onUpdate:modelValue"];
  var _hoisted_9 = { class: "input-group input-group-sm mb-3" };
  var _hoisted_10 = ["onUpdate:modelValue"];
  var _hoisted_11 = { class: "input-group input-group-sm mb-3" };
  var _hoisted_122 = ["onUpdate:modelValue"];
  var _hoisted_132 = { class: "input-group input-group-sm mb-3" };
  var _hoisted_142 = ["value", "onChange"];
  var _hoisted_15 = { class: "input-group input-group-sm mb-3" };
  var _hoisted_16 = ["onUpdate:modelValue"];
  var _hoisted_17 = ["onUpdate:modelValue"];
  var _hoisted_18 = ["onClick"];
  var _hoisted_19 = ["onClick"];
  var _hoisted_20 = { class: "input-group input-group-sm mb-3" };
  var _hoisted_21 = ["value"];
  var _hoisted_222 = ["onClick"];
  var _hoisted_232 = ["onClick"];
  var _hoisted_242 = { class: "header" };
  var _hoisted_25 = ["onClick"];
  var _hoisted_26 = { class: "input-group input-group-sm mb-1" };
  var _hoisted_27 = ["onUpdate:modelValue"];
  var _hoisted_28 = { class: "input-group input-group-sm mb-3" };
  var _hoisted_29 = ["value", "onChange"];
  var _hoisted_30 = ["onClick"];
  var _hoisted_31 = { class: "d-flex gap-2" };
  function render4(_ctx, _cache, $props, $setup, $data, $options) {
    return openBlock(), createElementBlock(
      Fragment,
      null,
      [
        createBaseVNode("div", _hoisted_14, [
          _cache[22] || (_cache[22] = createBaseVNode(
            "h3",
            null,
            "Files",
            -1
            /* HOISTED */
          )),
          (openBlock(true), createElementBlock(
            Fragment,
            null,
            renderList($props.releaseScript.files, (file, name) => {
              return openBlock(), createBlock(
                $setup["CollapsibleCard"],
                null,
                {
                  title: withCtx(() => [
                    createTextVNode(
                      toDisplayString(name) + " - " + toDisplayString(file.target.file) + " ",
                      1
                      /* TEXT */
                    ),
                    createBaseVNode(
                      "span",
                      _hoisted_24,
                      toDisplayString(file.sources.length) + " sources",
                      1
                      /* TEXT */
                    ),
                    file.needs.length > 0 ? (openBlock(), createElementBlock(
                      "span",
                      _hoisted_34,
                      toDisplayString(file.needs.length) + " dependencies",
                      1
                      /* TEXT */
                    )) : createCommentVNode("v-if", true)
                  ]),
                  buttons: withCtx(() => [
                    createBaseVNode("button", {
                      class: "btn btn-primary btn-sm btn-circle",
                      onClick: ($event) => $setup.renameFile($event, name)
                    }, [..._cache[1] || (_cache[1] = [
                      createBaseVNode(
                        "i",
                        { class: "fa fa-edit" },
                        null,
                        -1
                        /* HOISTED */
                      )
                    ])], 8, _hoisted_42),
                    createBaseVNode("button", {
                      class: "btn btn-danger btn-sm btn-circle",
                      onClick: ($event) => $setup.deleteFile($event, name)
                    }, [..._cache[2] || (_cache[2] = [
                      createBaseVNode(
                        "i",
                        { class: "fa fa-trash" },
                        null,
                        -1
                        /* HOISTED */
                      )
                    ])], 8, _hoisted_5)
                  ]),
                  body: withCtx(() => [
                    createBaseVNode("div", _hoisted_6, [
                      _cache[15] || (_cache[15] = createBaseVNode(
                        "h6",
                        null,
                        "Target settings",
                        -1
                        /* HOISTED */
                      )),
                      _cache[16] || (_cache[16] = createBaseVNode(
                        "p",
                        { class: "text-body-secondary" },
                        "Define the location of the target file in the repository and define the IRI of the resulting ontology.",
                        -1
                        /* HOISTED */
                      )),
                      createBaseVNode("div", _hoisted_7, [
                        withDirectives(createBaseVNode("input", {
                          "onUpdate:modelValue": ($event) => file.target.publish = $event,
                          class: "form-check-input",
                          type: "checkbox",
                          role: "switch"
                        }, null, 8, _hoisted_8), [
                          [vModelCheckbox, file.target.publish]
                        ]),
                        _cache[3] || (_cache[3] = createBaseVNode(
                          "span",
                          { class: "form-check-label" },
                          "Publish the file to GitHub",
                          -1
                          /* HOISTED */
                        ))
                      ]),
                      createBaseVNode("div", _hoisted_9, [
                        _cache[4] || (_cache[4] = createBaseVNode(
                          "span",
                          { class: "input-group-text" },
                          "Path",
                          -1
                          /* HOISTED */
                        )),
                        withDirectives(createBaseVNode("input", {
                          "onUpdate:modelValue": ($event) => file.target.file = $event,
                          type: "text",
                          class: "form-control"
                        }, null, 8, _hoisted_10), [
                          [vModelText, file.target.file]
                        ])
                      ]),
                      createBaseVNode("div", _hoisted_11, [
                        _cache[5] || (_cache[5] = createBaseVNode(
                          "span",
                          { class: "input-group-text" },
                          "IRI",
                          -1
                          /* HOISTED */
                        )),
                        withDirectives(createBaseVNode("input", {
                          "onUpdate:modelValue": ($event) => file.target.iri = $event,
                          type: "text",
                          class: "form-control"
                        }, null, 8, _hoisted_122), [
                          [vModelText, file.target.iri]
                        ])
                      ]),
                      createBaseVNode("div", _hoisted_132, [
                        _cache[6] || (_cache[6] = createBaseVNode(
                          "span",
                          { class: "input-group-text" },
                          "Annotations",
                          -1
                          /* HOISTED */
                        )),
                        createBaseVNode("textarea", {
                          value: Object.entries(file.target.ontology_annotations).map(([k, v]) => `${k}: ${v}`).join("\n"),
                          onChange: ($event) => $setup.setAnnotations(name, $event.target?.value),
                          class: "form-control"
                        }, "            ", 40, _hoisted_142)
                      ]),
                      _cache[17] || (_cache[17] = createBaseVNode(
                        "h6",
                        null,
                        "Source settings",
                        -1
                        /* HOISTED */
                      )),
                      _cache[18] || (_cache[18] = createBaseVNode(
                        "p",
                        { class: "text-body-secondary" },
                        " Add files that contain terms, individuals, and relations which should be included in the OWL ontology. Alternatively, add previously built owl files which should be merged to built the target ontology. ",
                        -1
                        /* HOISTED */
                      )),
                      (openBlock(true), createElementBlock(
                        Fragment,
                        null,
                        renderList(file.sources, (source) => {
                          return openBlock(), createElementBlock("div", _hoisted_15, [
                            _cache[9] || (_cache[9] = createBaseVNode(
                              "span",
                              { class: "input-group-text" },
                              "Source",
                              -1
                              /* HOISTED */
                            )),
                            withDirectives(createBaseVNode("input", {
                              "onUpdate:modelValue": ($event) => source.file = $event,
                              type: "text",
                              class: "form-control"
                            }, null, 8, _hoisted_16), [
                              [vModelText, source.file]
                            ]),
                            _cache[10] || (_cache[10] = createBaseVNode(
                              "span",
                              { class: "input-group-text" },
                              "Type",
                              -1
                              /* HOISTED */
                            )),
                            withDirectives(createBaseVNode("select", {
                              "onUpdate:modelValue": ($event) => source.type = $event,
                              class: "form-select",
                              style: { "flex": "unset", "width": "auto" }
                            }, [..._cache[7] || (_cache[7] = [
                              createBaseVNode(
                                "option",
                                { value: "classes" },
                                "Classes",
                                -1
                                /* HOISTED */
                              ),
                              createBaseVNode(
                                "option",
                                { value: "relations" },
                                "Relations",
                                -1
                                /* HOISTED */
                              ),
                              createBaseVNode(
                                "option",
                                { value: "individuals" },
                                "Individuals",
                                -1
                                /* HOISTED */
                              ),
                              createBaseVNode(
                                "option",
                                { value: "owl" },
                                "OWL",
                                -1
                                /* HOISTED */
                              )
                            ])], 8, _hoisted_17), [
                              [vModelSelect, source.type]
                            ]),
                            createBaseVNode("button", {
                              class: "btn btn-danger",
                              onClick: ($event) => file.sources = file.sources.filter((x) => x != source)
                            }, [..._cache[8] || (_cache[8] = [
                              createBaseVNode(
                                "i",
                                { class: "fa fa-trash" },
                                null,
                                -1
                                /* HOISTED */
                              )
                            ])], 8, _hoisted_18)
                          ]);
                        }),
                        256
                        /* UNKEYED_FRAGMENT */
                      )),
                      createBaseVNode("button", {
                        class: "mb-3 btn btn-sm btn-primary add-dependency",
                        onClick: ($event) => file.sources.push({ file: "", type: "classes" })
                      }, [..._cache[11] || (_cache[11] = [
                        createBaseVNode(
                          "i",
                          { class: "fa fa-add" },
                          null,
                          -1
                          /* HOISTED */
                        ),
                        createTextVNode(" Add source ")
                      ])], 8, _hoisted_19),
                      _cache[19] || (_cache[19] = createBaseVNode(
                        "h6",
                        null,
                        "Dependency settings",
                        -1
                        /* HOISTED */
                      )),
                      _cache[20] || (_cache[20] = createBaseVNode(
                        "p",
                        { class: "text-body-secondary" },
                        " Specify which other files have to be loaded when building this file. ",
                        -1
                        /* HOISTED */
                      )),
                      (openBlock(true), createElementBlock(
                        Fragment,
                        null,
                        renderList(file.needs, (need) => {
                          return openBlock(), createElementBlock("div", _hoisted_20, [
                            _cache[13] || (_cache[13] = createBaseVNode(
                              "span",
                              { class: "input-group-text" },
                              "Dependency",
                              -1
                              /* HOISTED */
                            )),
                            createBaseVNode("input", {
                              disabled: "",
                              value: $props.releaseScript.files[need]?.target.file ?? need,
                              type: "text",
                              class: "form-control"
                            }, null, 8, _hoisted_21),
                            createBaseVNode("button", {
                              onClick: ($event) => $setup.deleteDependency(name, need),
                              class: "btn btn-danger"
                            }, [..._cache[12] || (_cache[12] = [
                              createBaseVNode(
                                "i",
                                { class: "fa fa-trash" },
                                null,
                                -1
                                /* HOISTED */
                              )
                            ])], 8, _hoisted_222)
                          ]);
                        }),
                        256
                        /* UNKEYED_FRAGMENT */
                      )),
                      createBaseVNode("button", {
                        class: "mb-3 btn btn-sm btn-primary add-dependency",
                        onClick: ($event) => $setup.addDependency(name)
                      }, [..._cache[14] || (_cache[14] = [
                        createBaseVNode(
                          "i",
                          { class: "fa fa-add" },
                          null,
                          -1
                          /* HOISTED */
                        ),
                        createTextVNode(" Add dependency ")
                      ])], 8, _hoisted_232)
                    ])
                  ]),
                  _: 2
                  /* DYNAMIC */
                },
                1024
                /* DYNAMIC_SLOTS */
              );
            }),
            256
            /* UNKEYED_FRAGMENT */
          )),
          createBaseVNode("div", { class: "d-flex gap-2" }, [
            createBaseVNode("button", {
              class: "mb-3 btn btn-sm btn-primary add-file",
              onClick: $setup.addFile
            }, _cache[21] || (_cache[21] = [
              createBaseVNode(
                "i",
                { class: "fa fa-add" },
                null,
                -1
                /* HOISTED */
              ),
              createTextVNode(" Add file ")
            ]))
          ])
        ]),
        _cache[29] || (_cache[29] = createBaseVNode(
          "h3",
          null,
          "Steps",
          -1
          /* HOISTED */
        )),
        createBaseVNode("button", {
          class: "btn btn-outline-primary add-step mb-3",
          onClick: _cache[0] || (_cache[0] = ($event) => $setup.addStep($event, 0))
        }, _cache[23] || (_cache[23] = [
          createBaseVNode(
            "i",
            { class: "fa fa-plus-square" },
            null,
            -1
            /* HOISTED */
          ),
          createTextVNode(" Add step here ")
        ])),
        (openBlock(true), createElementBlock(
          Fragment,
          null,
          renderList($props.releaseScript.steps, (step, index) => {
            return openBlock(), createElementBlock(
              Fragment,
              null,
              [
                createBaseVNode("div", _hoisted_242, [
                  createBaseVNode(
                    "h6",
                    null,
                    toDisplayString(step.name),
                    1
                    /* TEXT */
                  ),
                  _cache[25] || (_cache[25] = createBaseVNode(
                    "span",
                    null,
                    null,
                    -1
                    /* HOISTED */
                  )),
                  createBaseVNode("button", {
                    class: "btn btn-danger btn-sm btn-circle",
                    style: { "margin-bottom": ".5rem" },
                    onClick: ($event) => $setup.deleteStep($event, index)
                  }, [..._cache[24] || (_cache[24] = [
                    createBaseVNode(
                      "i",
                      { class: "fa fa-trash" },
                      null,
                      -1
                      /* HOISTED */
                    )
                  ])], 8, _hoisted_25)
                ]),
                createBaseVNode("div", _hoisted_26, [
                  _cache[26] || (_cache[26] = createBaseVNode(
                    "span",
                    { class: "input-group-text" },
                    "Release step",
                    -1
                    /* HOISTED */
                  )),
                  withDirectives(createBaseVNode("input", {
                    "onUpdate:modelValue": ($event) => step.name = $event,
                    class: "form-control",
                    type: "text"
                  }, null, 8, _hoisted_27), [
                    [vModelText, step.name]
                  ])
                ]),
                createBaseVNode("div", _hoisted_28, [
                  _cache[27] || (_cache[27] = createBaseVNode(
                    "span",
                    { class: "input-group-text" },
                    "Arguments",
                    -1
                    /* HOISTED */
                  )),
                  createBaseVNode("textarea", {
                    value: Object.entries(step.args).map(([k, v]) => `${k}: ${v}`).join("\n"),
                    class: "form-control",
                    onChange: ($event) => $setup.setArgs(index, $event.target?.value)
                  }, "            ", 40, _hoisted_29)
                ]),
                createBaseVNode("button", {
                  class: "btn btn-outline-primary add-step mb-3",
                  onClick: ($event) => $setup.addStep($event, index + 1)
                }, [..._cache[28] || (_cache[28] = [
                  createBaseVNode(
                    "i",
                    { class: "fa fa-plus-square" },
                    null,
                    -1
                    /* HOISTED */
                  ),
                  createTextVNode(" Add step here ")
                ])], 8, _hoisted_30)
              ],
              64
              /* STABLE_FRAGMENT */
            );
          }),
          256
          /* UNKEYED_FRAGMENT */
        )),
        createBaseVNode("div", _hoisted_31, [
          renderSlot(_ctx.$slots, "buttons", {}, void 0, true)
        ])
      ],
      64
      /* STABLE_FRAGMENT */
    );
  }

  // js/release/ReleaseScriptViewer.vue
  ReleaseScriptViewer_default.render = render4;
  ReleaseScriptViewer_default.__file = "js/release/ReleaseScriptViewer.vue";
  ReleaseScriptViewer_default.__scopeId = "data-v-033a957d";
  var ReleaseScriptViewer_default2 = ReleaseScriptViewer_default;

  // sfc-script:/home/bjoern/development/onto-spread-ed/js/release/Setup.vue?type=script
  var Setup_default = /* @__PURE__ */ defineComponent({
    __name: "Setup",
    props: {
      repo: { type: String, required: false }
    },
    emits: ["settingsConfirmed"],
    setup(__props, { expose: __expose }) {
      __expose();
      const showAdvanced = ref();
      const releaseScript = ref(null);
      const prefix_url2 = URLS.prefix;
      const saving = ref("idle");
      const props = __props;
      const lastReleases = ref(null);
      const loading = computed2(() => lastReleases.value === null);
      const lastSuccessfulRelease = computed2(() => lastReleases.value?.find((x) => x.state === "completed") ?? null);
      const lastRelease = computed2(() => lastReleases.value?.[0] ?? null);
      watch2(props, (value, oldValue) => value.repo !== oldValue.repo && update());
      async function update() {
        if (props.repo) {
          releaseScript.value = null;
          releaseScript.value = await (await fetch(`${prefix_url2}/api/release/${props.repo}/release_script`)).json();
          const releases = await (await fetch(`${prefix_url2}/api/release/${props.repo}`)).json();
          releases.sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime());
          lastReleases.value = releases;
        }
      }
      let _saveFileAnimationTimeout = null;
      async function saveFile($event) {
        $event.preventDefault();
        if (_saveFileAnimationTimeout !== null) {
          clearTimeout(_saveFileAnimationTimeout);
        }
        saving.value = "saving";
        try {
          const response = await fetch(`${prefix_url2}/api/release/${props.repo}/release_script`, {
            method: "PUT",
            headers: {
              "Content-Type": "application/json"
            },
            body: JSON.stringify(releaseScript.value)
          });
          if (response.ok) {
            saving.value = "success";
          } else {
            saving.value = "error";
          }
        } catch (e) {
          saving.value = "error";
        }
        _saveFileAnimationTimeout = setTimeout(() => {
          saving.value = "idle";
          _saveFileAnimationTimeout = null;
        }, 5e3);
      }
      onMounted(() => update());
      const __returned__ = { showAdvanced, releaseScript, prefix_url: prefix_url2, saving, props, lastReleases, loading, lastSuccessfulRelease, lastRelease, update, get _saveFileAnimationTimeout() {
        return _saveFileAnimationTimeout;
      }, set _saveFileAnimationTimeout(v) {
        _saveFileAnimationTimeout = v;
      }, saveFile, ReleaseScriptViewer: ReleaseScriptViewer_default2 };
      Object.defineProperty(__returned__, "__isScriptSetup", { enumerable: false, value: true });
      return __returned__;
    }
  });

  // sfc-template:/home/bjoern/development/onto-spread-ed/js/release/Setup.vue?type=template
  var _hoisted_110 = { class: "preparation" };
  var _hoisted_210 = {
    key: 0,
    style: { "width": "400px" },
    class: "placeholder"
  };
  var _hoisted_35 = { class: "btn-group w-100" };
  var _hoisted_43 = ["disabled"];
  var _hoisted_52 = ["disabled"];
  var _hoisted_62 = { class: "dropdown-menu" };
  var _hoisted_72 = {
    key: 0,
    class: "fa fa-save"
  };
  var _hoisted_82 = {
    key: 1,
    class: "fa fa-spin fa-spinner"
  };
  var _hoisted_92 = {
    key: 2,
    class: "fa fa-check"
  };
  var _hoisted_102 = {
    key: 3,
    class: "fa fa-xmark"
  };
  function render5(_ctx, _cache, $props, $setup, $data, $options) {
    return openBlock(), createElementBlock("div", _hoisted_110, [
      _cache[5] || (_cache[5] = createBaseVNode(
        "h3",
        null,
        "Release setup",
        -1
        /* HOISTED */
      )),
      createBaseVNode("p", null, [
        createTextVNode(
          " Currently, there is no release running for " + toDisplayString($props.repo) + ". ",
          1
          /* TEXT */
        ),
        $setup.loading ? (openBlock(), createElementBlock("span", _hoisted_210)) : $setup.lastSuccessfulRelease ? (openBlock(), createElementBlock(
          Fragment,
          { key: 1 },
          [
            createTextVNode(
              toDisplayString($setup.lastSuccessfulRelease.started_by) + " started the last successful release on " + toDisplayString(_ctx.$filters.formatDate($setup.lastSuccessfulRelease.start)),
              1
              /* TEXT */
            )
          ],
          64
          /* STABLE_FRAGMENT */
        )) : $setup.lastRelease ? (openBlock(), createElementBlock(
          Fragment,
          { key: 2 },
          [
            createTextVNode(
              toDisplayString($setup.lastRelease.started_by) + " started the last release on " + toDisplayString(_ctx.$filters.formatDate($setup.lastRelease.start)) + ". But it did not complete. ",
              1
              /* TEXT */
            )
          ],
          64
          /* STABLE_FRAGMENT */
        )) : (openBlock(), createElementBlock(
          Fragment,
          { key: 3 },
          [
            createTextVNode(" There have been no releases in the near past. ")
          ],
          64
          /* STABLE_FRAGMENT */
        ))
      ]),
      createBaseVNode("div", _hoisted_35, [
        createBaseVNode("button", {
          disabled: !$setup.releaseScript,
          class: "btn btn-success",
          onClick: _cache[0] || (_cache[0] = ($event) => _ctx.$emit("settingsConfirmed", $setup.releaseScript))
        }, _cache[2] || (_cache[2] = [
          createBaseVNode(
            "i",
            { class: "fa fa-play" },
            null,
            -1
            /* HOISTED */
          ),
          createTextVNode(" Start a release ")
        ]), 8, _hoisted_43),
        createBaseVNode("button", {
          disabled: !$setup.releaseScript,
          type: "button",
          class: "btn btn-success dropdown-toggle dropdown-toggle-split flex-grow-0",
          "data-bs-toggle": "dropdown"
        }, null, 8, _hoisted_52),
        createBaseVNode("ul", _hoisted_62, [
          createBaseVNode("li", null, [
            createBaseVNode("a", {
              class: "dropdown-item",
              href: "#",
              onClick: _cache[1] || (_cache[1] = ($event) => $setup.showAdvanced = !$setup.showAdvanced)
            }, [
              createBaseVNode(
                "i",
                {
                  class: normalizeClass(["fa-regular", [$setup.showAdvanced ? "fa-check-square" : "fa-square"]])
                },
                null,
                2
                /* CLASS */
              ),
              _cache[3] || (_cache[3] = createTextVNode(" Show advanced configuration "))
            ])
          ])
        ])
      ]),
      !!$setup.releaseScript && $setup.showAdvanced ? (openBlock(), createBlock($setup["ReleaseScriptViewer"], {
        key: 0,
        "release-script": $setup.releaseScript,
        class: "mt-2"
      }, {
        buttons: withCtx(() => [
          createBaseVNode(
            "button",
            {
              class: normalizeClass(["mb-3 btn btn-sm btn-primary", {
                "btn-primary": $setup.saving === "idle" || $setup.saving === "saving",
                "btn-success": $setup.saving === "success",
                "btn-danger": $setup.saving === "error"
              }]),
              onClick: $setup.saveFile
            },
            [
              $setup.saving === "idle" ? (openBlock(), createElementBlock("i", _hoisted_72)) : createCommentVNode("v-if", true),
              $setup.saving === "saving" ? (openBlock(), createElementBlock("i", _hoisted_82)) : createCommentVNode("v-if", true),
              $setup.saving === "success" ? (openBlock(), createElementBlock("i", _hoisted_92)) : createCommentVNode("v-if", true),
              $setup.saving === "error" ? (openBlock(), createElementBlock("i", _hoisted_102)) : createCommentVNode("v-if", true),
              _cache[4] || (_cache[4] = createTextVNode(" Save release script "))
            ],
            2
            /* CLASS */
          )
        ]),
        _: 1
        /* STABLE */
      }, 8, ["release-script"])) : createCommentVNode("v-if", true)
    ]);
  }

  // js/release/Setup.vue
  Setup_default.render = render5;
  Setup_default.__file = "js/release/Setup.vue";
  var Setup_default2 = Setup_default;

  // sfc-script:/home/bjoern/development/onto-spread-ed/js/release/ErrorLink.vue?type=script
  var ErrorLink_default = /* @__PURE__ */ defineComponent({
    __name: "ErrorLink",
    props: {
      short_repository_name: { type: String, required: true },
      error: { type: Object, required: false },
      term: { type: Object, required: false }
    },
    setup(__props, { expose: __expose }) {
      __expose();
      const props = __props;
      const item = computed2(() => !!props.term ? props.term : props.error);
      const prefix_url2 = URLS.prefix;
      const __returned__ = { props, item, prefix_url: prefix_url2 };
      Object.defineProperty(__returned__, "__isScriptSetup", { enumerable: false, value: true });
      return __returned__;
    }
  });

  // sfc-template:/home/bjoern/development/onto-spread-ed/js/release/ErrorLink.vue?type=template
  var _hoisted_111 = ["href"];
  function render6(_ctx, _cache, $props, $setup, $data, $options) {
    return $setup.item.hasOwnProperty("origin") && $setup.item.origin ? (openBlock(), createElementBlock("a", {
      key: 0,
      target: "_blank",
      href: `${$setup.prefix_url}/edit/${$props.short_repository_name}/${$setup.item.origin[0]}?row=${$setup.item.origin[1]}`
    }, [
      renderSlot(_ctx.$slots, "default", {}, () => [
        createBaseVNode("i", null, [
          _cache[3] || (_cache[3] = createTextVNode(" at ")),
          createBaseVNode(
            "b",
            null,
            toDisplayString($setup.item.origin[0]),
            1
            /* TEXT */
          ),
          $props.error && "row" in $props.error ? (openBlock(), createElementBlock(
            Fragment,
            { key: 0 },
            [
              _cache[0] || (_cache[0] = createTextVNode(" row ")),
              createBaseVNode(
                "b",
                null,
                toDisplayString($props.error["row"]),
                1
                /* TEXT */
              )
            ],
            64
            /* STABLE_FRAGMENT */
          )) : createCommentVNode("v-if", true),
          $props.error && "column" in $props.error ? (openBlock(), createElementBlock(
            Fragment,
            { key: 1 },
            [
              _cache[1] || (_cache[1] = createTextVNode(" column ")),
              createBaseVNode(
                "b",
                null,
                toDisplayString($props.error.column),
                1
                /* TEXT */
              )
            ],
            64
            /* STABLE_FRAGMENT */
          )) : createCommentVNode("v-if", true),
          !$props.error && $setup.item.origin[1] >= 0 ? (openBlock(), createElementBlock(
            Fragment,
            { key: 2 },
            [
              _cache[2] || (_cache[2] = createTextVNode(" row ")),
              createBaseVNode(
                "b",
                null,
                toDisplayString($setup.item.origin[1]),
                1
                /* TEXT */
              )
            ],
            64
            /* STABLE_FRAGMENT */
          )) : createCommentVNode("v-if", true)
        ])
      ])
    ], 8, _hoisted_111)) : createCommentVNode("v-if", true);
  }

  // js/release/ErrorLink.vue
  ErrorLink_default.render = render6;
  ErrorLink_default.__file = "js/release/ErrorLink.vue";
  var ErrorLink_default2 = ErrorLink_default;

  // js/common/bootbox.ts
  function promptDialog(options) {
    return new Promise((resolve2) => {
      bootbox.prompt({
        ...options,
        callback(result) {
          resolve2(result ?? null);
        }
      });
    });
  }
  function confirmDialog(options) {
    return new Promise((resolve2) => {
      bootbox.confirm({
        ...options,
        callback(result) {
          resolve2(result);
        }
      });
    });
  }

  // js/release/autofix/guessParent.ts
  var prefix_url = URLS.prefix;
  async function guessExternal(term, _, defined_parent) {
    try {
      const response = await fetch(`${prefix_url}/api/external/guess-parent`, {
        method: "post",
        body: JSON.stringify({
          term: {
            id: term.id ?? void 0,
            label: term.label ?? void 0
          },
          parent: {
            id: defined_parent?.id ?? void 0,
            label: defined_parent?.label ?? void 0
          }
        }),
        headers: {
          "Content-Type": "application/json"
        }
      });
      const parent = await response.json();
      if (parent) {
        return parent.map((x) => ({ ...x, kind: "external" }));
      }
    } catch {
    }
    return null;
  }
  async function singleExternalGuess(error, repo, guess) {
    const parent = guess.term;
    const result = await confirmDialog({
      title: "Found an external parent",
      message: `An external parent <code>${parent.label}</code> (<code>${parent.id}</code>) of <code>${error.term.label}</code> (<code>${error.term.id}</code>) was found. Import the term?`,
      buttons: {
        confirm: {
          label: `Import ${parent.id}`,
          className: "btn-success"
        },
        cancel: {
          label: "Cancel",
          className: "btn-warning"
        }
      }
    });
    if (result) {
      try {
        const response = await fetch(`${prefix_url}/api/external/${repo}/import`, {
          method: "post",
          body: JSON.stringify({
            terms: [{ id: parent.id, label: parent.label }],
            ontologyId: guess.ontology_id
          }),
          headers: { "Content-Type": "application/json" }
        });
        if (response.ok) {
          return "fixed";
        }
      } catch {
        return "impossible";
      }
    }
    return "loaded";
  }
  async function multipleExternalGuesses(guesses, error, repo) {
    const index = await promptDialog({
      title: "Found possible external parents",
      message: `Found ${guesses.length} possible external terms for <code>${error.parent.label}</code>. Select the correct parent term of <code>${error.term.label}</code> (<code>${error.term.id}</code>) if it is in the list.`,
      inputType: "select",
      inputOptions: guesses.map((g, i) => ({ value: i.toString(), text: `${g.term.label} (${g.term.id})` })),
      buttons: {
        confirm: {
          label: `Import the selected term`,
          className: "btn-success"
        },
        cancel: {
          label: "Cancel",
          className: "btn-warning"
        }
      }
    });
    if (index !== null) {
      const guess = guesses[+index];
      const parent = guess.term;
      try {
        const response = await fetch(`${prefix_url}/api/external/${repo}/import`, {
          method: "post",
          body: JSON.stringify({
            terms: [{
              id: parent.id,
              label: parent.label
            }],
            ontologyId: guess.ontology_id
          }),
          headers: { "Content-Type": "application/json" }
        });
        if (response.ok) {
          return "fixed";
        } else {
          return "impossible";
        }
      } catch {
        return "impossible";
      }
    }
    return "loaded";
  }
  async function guessParent(error, repo) {
    const guesses = await guessExternal(error.term, repo, error.parent);
    if (guesses !== null && guesses.length > 0) {
      if (guesses.length === 1) {
        return await singleExternalGuess(error, repo, guesses[0]);
      } else {
        return await multipleExternalGuesses(guesses, error, repo);
      }
    }
    return "impossible";
  }

  // js/common/diagnostic-data.ts
  var DIAGNOSTIC_DATA = {
    "unknown-parent": {
      severity: "error",
      title: (d) => `Unknown parent`,
      message: (d) => `The parent <code>${d.parent.label}</code> of <code>${(d.term ?? d.relation).label}</code>
              (<code>${(d.term ?? d.relation).id || "no id"}</code>) is not known.`
    },
    "missing-parent": {
      severity: "error",
      title: (d) => `Missing parent`,
      message: (d) => `The parent <code>${d.parent.label}</code> (<code>${d.parent.id}</code>) of
              <code>${d.term.label}</code>
              (<code>${d.term.id || "no id"}) is neither defined in the Excel files or imported.
              If it is an external term, add the missing import the entry with
              <code>${d.parent.label} [${d.parent.id}]</code>.`
    },
    "no-parent": {
      severity: "error",
      title: (d) => `Term has no parent`,
      message: (d) => `The term <code>${d.term.label}</code> (<code>${d.term.id ?? "no id"}</code>) has no parent!`
    },
    "ignored-parent": {
      severity: "error",
      title: (d) => `${d.status} parent`,
      message: (d) => `The parent <code>${d.parent.label}</code> of <code>${d.term.label}</code>
              (<code>${d.term.id ?? "no id"}</code>) is ${d.status.toLowerCase()}.<br>`
    },
    "missing-label": {
      severity: "error",
      title: (d) => `Missing label`,
      message: (d) => `The term <code>${d.term.id}</code> has no label.`
    },
    "missing-id": {
      severity: "error",
      title: (d) => `Term has no ID`,
      message: (d) => `              The term <code>${d.term.label}</code> has no ID but is also not obsolete or pre-proposed. <br>`
    },
    "unknown-disjoint": {
      severity: "error",
      title: (d) => `Unknown disjoint class`,
      message: (d) => `The class <code>${d.term.label}</code> (<code>${d.term.id ?? "no id"}</code>) is
              specified to
              be disjoint with <code>${d.disjoint_class.label}</code> but it is not known.<br>`
    },
    "missing-disjoint": {
      severity: "error",
      title: (d) => `Missing disjoint class`,
      message: (d) => `The disjoint class <code>${d.disjoint_class.label}</code> (<code>${d.disjoint_class.id}</code>) of 
              <code>${d.term.label}</code>
              (<code>${d.term.id || "no id"}) is neither defined in the Excel files or imported.
              If it is an external term, add the missing import the entry with
              <code>${d.disjoint_class.label} [${d.disjoint_class.id}]</code>.`
    },
    "ignored-disjoint": {
      severity: "error",
      title: (d) => `${d.status} disjoint class`,
      message: (d) => `The disjoint class <code>${d.disjoint_class.label}</code> of <code>${d.term.label}</code>
              (<code>${d.term.id ?? "no id"}</code>) is ${d.status.toLowerCase()}.<br>`
    },
    "unknown-relation-value": {
      severity: "error",
      title: (d) => `Unknown value for relation <code>${d.relation.label}</code>`,
      message: (d) => `Related term <code>${d.value.label}</code> of <code>${d.term.label}</code>
              (<code>${d.term.id || "no id"}
            </code>) for <code>${d.relation.label}</code> is not known.`
    },
    "missing-relation-value": {
      severity: "error",
      title: (d) => `Unknown value for relation <code>${d.relation.label}</code>`,
      message: (d) => `Related term <code>${d.value.label}</code> of 
              <code>${d.term.label}</code>
              (<code>${d.term.id || "no id"}) is neither defined in the Excel files or imported.
              If it is an external term, add the missing import the entry with
              <code>${d.value.label} [${d.value.id}]</code>.`
    },
    "ignored-relation-value": {
      severity: "error",
      title: (d) => `${d.status} value for relation <code>${d.relation.label}</code>`,
      message: (d) => `Related term <code>${d.value.label}</code> of <code>${d.term.label}</code>
              (<code>${d.term.id ?? "no id"}</code>) is ${d.status.toLowerCase()}.`
    },
    "unknown-range": {
      severity: "error",
      title: (d) => `Unknown range`,
      message: (d) => `The range <code>${d.relation.range.label}</code> of
              <code>${d.relation.label}</code>
              (<code>${d.relation.id || "no id"}
            </code>) is not known. `
    },
    "missing-range": {
      severity: "error",
      title: (d) => `Missing range`,
      message: (d) => `The range <code>${d.relation.range.label}</code> of 
              <code>${d.relation.label}</code>
              (<code>${d.relation.id || "no id"}) is neither defined in the Excel files or imported.
              If it is an external term, add the missing import the entry with
              <code>${d.range.label} [${d.range.id}]</code>.`
    },
    "ignored-range": {
      severity: "error",
      title: (d) => `${d.status} range`,
      message: (d) => `The range <code>${d.range.label}</code> of <code>${d.relation.label}</code>
              (<code>${d.relation.id ?? "no id"}</code>) is ${d.status.toLowerCase()}.<br>`
    },
    "unknown-domain": {
      severity: "error",
      title: (d) => `Unknown domain`,
      message: (d) => `The domain <code>${d.relation.domain.label}</code> of
              <code>${d.relation.label}</code>
              (<code>${d.relation.id || "no id"} </code>) is not known.`
    },
    "missing-domain": {
      severity: "error",
      title: (d) => `Missing domain`,
      message: (d) => `The domain <code>${d.relation.domain.label}</code> of 
              <code>${d.relation.label}</code>
              (<code>${d.relation.id || "no id"}) is neither defined in the Excel files or imported.
              If it is an external term, add the missing import the entry with
              <code>${d.domain.label} [${d.domain.id}]</code>.`
    },
    "ignored-domain": {
      severity: "error",
      title: (d) => `${d.status} domain`,
      message: (d) => `The domain <code>${d.domain.label}</code> of <code>${d.relation.label}</code>
              (<code>${d.relation.id ?? "no id"}</code>) is ${d.status.toLowerCase()}.<br>`
    },
    "unknown-relation": {
      severity: "error",
      title: (d) => `Unknown relation`,
      message: (d) => `The relation ${d.relation.label ? `<code>${d.relation.label}</code>` + (d.relation.id ? "(" + d.relation.id + ")" : "") : d.relation.id} is not known`
    },
    "duplicate": {
      severity: "error",
      title: (d) => `Conflicting entries (duplicates)`,
      message: (d) => `There are multiple terms for the ${d.duplicate_field} <code>${d.duplicate_value}</code>:`
    },
    "incomplete-term": {
      severity: "warning",
      title: (d) => `Incomplete term`,
      message: (d) => `There is an incomplete term with no an ID, a label, or a parent defined. Is there an empty line in the
              spreadsheet? The line is ignored`
    },
    "unknown-column": {
      severity: "warning",
      title: (d) => `Unmapped column`,
      message: (d) => `The column <code>${d.column}</code> of <code>${d.sheet}</code> is not mapped
              to any OWL property or internal field.`
    },
    "missing-import": {
      severity: "warning",
      title: (d) => `Missing import`,
      message: (d) => `The term <code>${d.term.label}</code> (<code>${d.term.id ?? "no id"}</code>) has the curation
              status
              "External" but is not included in the externally imported terms.` + (d.term.id ? ` Does the term still exist in
                ${d.term.id.split(":")[0]}?` : "")
    },
    "inconsistent-import": {
      severity: "warning",
      title: (d) => `Inconsistent import`,
      message: (d) => `The term <code>${d.term.label}</code> (<code>${d.term.id ?? "no id"}</code>) has the curation
              status "External" but its ` + (d.term.id !== d.imported_term.id ? `ID (<code>${d.imported_term.id}</code>)` : `label (<code>${d.imported_term.label}</code>)`) + ` differs.`
    }
  };

  // sfc-script:/home/bjoern/development/onto-spread-ed/js/common/Diagnostic.vue?type=script
  var Diagnostic_default = /* @__PURE__ */ defineComponent({
    __name: "Diagnostic",
    props: {
      diagnostic: { type: Object, required: true },
      severity: { type: [String, null], required: false, default: null },
      format: { type: String, required: false, default: "long" }
    },
    setup(__props, { expose: __expose }) {
      __expose();
      const props = __props;
      const badgeClasses = computed2(() => ({
        "text-bg-danger": (props.severity ?? data.value.severity) === "error",
        "text-bg-warning": (props.severity ?? data.value.severity) === "warning",
        "text-bg-info": (props.severity ?? data.value.severity) === "info"
      }));
      const data = computed2(() => ({
        severity: DIAGNOSTIC_DATA[props.diagnostic.type].severity,
        title: DIAGNOSTIC_DATA[props.diagnostic.type].title(props.diagnostic),
        message: DIAGNOSTIC_DATA[props.diagnostic.type].message(props.diagnostic)
      }));
      const __returned__ = { props, badgeClasses, data };
      Object.defineProperty(__returned__, "__isScriptSetup", { enumerable: false, value: true });
      return __returned__;
    }
  });

  // sfc-template:/home/bjoern/development/onto-spread-ed/js/common/Diagnostic.vue?type=template
  var _hoisted_112 = ["innerHTML"];
  var _hoisted_211 = { key: 0 };
  var _hoisted_36 = { key: 1 };
  var _hoisted_44 = ["innerHTML"];
  function render7(_ctx, _cache, $props, $setup, $data, $options) {
    return $props.format === "long" ? (openBlock(), createElementBlock(
      Fragment,
      { key: 0 },
      [
        createBaseVNode(
          "h5",
          null,
          toDisplayString($setup.data.title),
          1
          /* TEXT */
        ),
        createBaseVNode("p", {
          innerHTML: $setup.data.message
        }, null, 8, _hoisted_112),
        _ctx.$slots.default ? (openBlock(), createElementBlock("p", _hoisted_211, [
          renderSlot(_ctx.$slots, "default")
        ])) : createCommentVNode("v-if", true)
      ],
      64
      /* STABLE_FRAGMENT */
    )) : $props.format === "inline" ? (openBlock(), createElementBlock("p", _hoisted_36, [
      createBaseVNode("span", {
        innerHTML: $setup.data.message
      }, null, 8, _hoisted_44)
    ])) : $props.format === "text" ? (openBlock(), createElementBlock(
      Fragment,
      { key: 2 },
      [
        createTextVNode(
          toDisplayString($setup.data.message.replace(/(<([^>]+)>)/ig, "")),
          1
          /* TEXT */
        )
      ],
      64
      /* STABLE_FRAGMENT */
    )) : createCommentVNode("v-if", true);
  }

  // js/common/Diagnostic.vue
  Diagnostic_default.render = render7;
  Diagnostic_default.__file = "js/common/Diagnostic.vue";
  var Diagnostic_default2 = Diagnostic_default;

  // sfc-script:/home/bjoern/development/onto-spread-ed/js/release/steps/Validation.vue?type=script
  var Validation_default = /* @__PURE__ */ defineComponent({
    __name: "Validation",
    props: {
      data: { type: [Object, null], required: true },
      release: { type: Object, required: true },
      selectedSubStep: { type: [String, null], required: true }
    },
    emits: ["release-control"],
    setup(__props, { expose: __expose }) {
      __expose();
      const prefix_url2 = URLS.prefix;
      const props = __props;
      const autoFixStates = ref({});
      function autoFixState(diag) {
        const id = JSON.stringify(diag);
        return autoFixStates.value[id] ?? null;
      }
      const errors = computed2(() => {
        if (!props.data) {
          return null;
        }
        return Object.values(props.data).flatMap((v) => v.errors);
      });
      const warnings = computed2(() => {
        if (!props.data) {
          return null;
        }
        return Object.values(props.data).flatMap((v) => v.warnings);
      });
      const shortRepoName = computed2(() => props.release.release_script.short_repository_name);
      async function updateTerm(path, id, term) {
        const repo = props.release.release_script.short_repository_name;
        try {
          const response = await fetch(`${prefix_url2}/api/edit/${repo}/${path}`, {
            method: "PATCH",
            body: JSON.stringify({
              id,
              term: {
                id: term.id,
                parent: term.sub_class_of[0]?.label,
                label: term.label
              }
            }),
            headers: { "Content-Type": "application/json" }
          });
          if (response.ok) {
            return "fixed";
          } else {
            return "impossible";
          }
        } catch {
          return "impossible";
        }
      }
      async function autofixUpdateTerm(error, id, term, path) {
        const wid = JSON.stringify(error);
        if (wid in autoFixStates.value && autoFixStates.value[wid] !== "loaded") {
          return;
        }
        autoFixStates.value[wid] = await updateTerm(path ?? error?.term?.origin?.[0] ?? term?.origin?.[0], id, term);
      }
      async function autofix(error) {
        let id = JSON.stringify(error);
        if (id in autoFixStates.value && autoFixStates.value[id] !== "loaded") {
          return;
        }
        const repo = props.release.release_script.short_repository_name;
        autoFixStates.value[id] = "loading";
        if (error.type === "unknown-parent") {
          autoFixStates.value[id] = await guessParent(error, repo);
        } else if (error.type === "missing-import") {
          try {
            const response = await fetch(`${prefix_url2}/api/external/${repo}/import`, {
              method: "post",
              body: JSON.stringify({
                terms: [{ id: error.term.id, label: error.term.label }],
                ontologyId: error.term.id.split(":")[0]
              }),
              headers: { "Content-Type": "application/json" }
            });
            if (response.ok) {
              autoFixStates.value[id] = "fixed";
            }
          } catch (e) {
            autoFixStates.value[id] = "impossible";
            console.error(e);
          }
        } else {
          autoFixStates.value[id] = "impossible";
        }
        if (autoFixStates.value[id] == "loading") {
          autoFixStates.value[id] = "loaded";
        }
      }
      const __returned__ = { prefix_url: prefix_url2, props, autoFixStates, autoFixState, errors, warnings, shortRepoName, updateTerm, autofixUpdateTerm, autofix, ErrorLink: ErrorLink_default2, ProgressIndicator: ProgressIndicator_default2, Diagnostic: Diagnostic_default2 };
      Object.defineProperty(__returned__, "__isScriptSetup", { enumerable: false, value: true });
      return __returned__;
    }
  });

  // sfc-template:/home/bjoern/development/onto-spread-ed/js/release/steps/Validation.vue?type=template
  var _hoisted_113 = {
    key: 0,
    class: "alert alert-success"
  };
  var _hoisted_212 = { key: 1 };
  var _hoisted_37 = { class: "text-danger bg-danger-subtle rounded ps-1 pe-1" };
  var _hoisted_45 = { class: "text-warning bg-warning-subtle rounded ps-1 pe-1" };
  var _hoisted_53 = ["onClick"];
  var _hoisted_63 = {
    key: 0,
    class: "fa fa-spin fa-spinner"
  };
  var _hoisted_73 = {
    key: 1,
    class: "fa fa-check"
  };
  var _hoisted_83 = {
    key: 2,
    class: "fa fa-close"
  };
  var _hoisted_93 = { style: { "text-transform": "capitalize" } };
  var _hoisted_103 = { key: 0 };
  var _hoisted_114 = { key: 1 };
  var _hoisted_123 = { key: 2 };
  var _hoisted_133 = { key: 3 };
  var _hoisted_143 = {
    class: "alert alert-warning val val-warning val-warning-type-{{ warning.type }} val-warning-source-{{ source }}",
    role: "alert"
  };
  var _hoisted_152 = ["onClick"];
  var _hoisted_162 = {
    key: 0,
    class: "fa fa-spin fa-spinner"
  };
  var _hoisted_172 = {
    key: 1,
    class: "fa fa-check"
  };
  var _hoisted_182 = {
    key: 2,
    class: "fa fa-close"
  };
  var _hoisted_192 = ["onClick"];
  var _hoisted_202 = {
    key: 0,
    class: "fa fa-spin fa-spinner"
  };
  var _hoisted_213 = {
    key: 1,
    class: "fa fa-check"
  };
  var _hoisted_223 = {
    key: 2,
    class: "fa fa-close"
  };
  function render8(_ctx, _cache, $props, $setup, $data, $options) {
    return openBlock(), createElementBlock(
      Fragment,
      null,
      [
        _cache[18] || (_cache[18] = createBaseVNode(
          "h3",
          null,
          "Validation",
          -1
          /* HOISTED */
        )),
        !$props.data || Object.keys($props.data).length === 1 && "__progress" in $props.data ? (openBlock(), createBlock($setup["ProgressIndicator"], {
          key: 0,
          release: $props.release,
          details: $props.data || {}
        }, {
          default: withCtx(() => _cache[0] || (_cache[0] = [
            createTextVNode(" All excel files are now being validated. The results will be presented here soon. ")
          ])),
          _: 1
          /* STABLE */
        }, 8, ["release", "details"])) : (openBlock(), createElementBlock(
          Fragment,
          { key: 1 },
          [
            $setup.errors?.length == 0 && $setup.warnings?.length == 0 ? (openBlock(), createElementBlock("div", _hoisted_113, _cache[1] || (_cache[1] = [
              createBaseVNode(
                "h5",
                null,
                "Everything ok",
                -1
                /* HOISTED */
              ),
              createTextVNode(" Good work! All files are valid. The release process will continue. ")
            ]))) : (openBlock(), createElementBlock("p", _hoisted_212, [
              createBaseVNode(
                "span",
                _hoisted_37,
                toDisplayString($setup.errors?.length ?? 0) + " " + toDisplayString(_ctx.$filters.pluralise("error", $setup.errors)),
                1
                /* TEXT */
              ),
              _cache[2] || (_cache[2] = createTextVNode(" and ")),
              createBaseVNode(
                "span",
                _hoisted_45,
                toDisplayString($setup.warnings?.length ?? 0) + " " + toDisplayString(_ctx.$filters.pluralise("warning", $setup.warnings)),
                1
                /* TEXT */
              ),
              _cache[3] || (_cache[3] = createTextVNode(" were found during the validation. Please fix the errors and save the spreadsheets. Errors are problems which prevent the release from continuing. Warnings hint at possible problems, but the release might continue without solving them. When you fixed all errors, restart the release. If you just want to rerun the validation, restart the release as well. "))
            ])),
            (openBlock(true), createElementBlock(
              Fragment,
              null,
              renderList($props.data ? Object.keys($props.data) : [], (source) => {
                return openBlock(), createElementBlock(
                  Fragment,
                  null,
                  [
                    $props.selectedSubStep === null || $props.selectedSubStep === source ? (openBlock(), createElementBlock(
                      Fragment,
                      { key: 0 },
                      [
                        (openBlock(true), createElementBlock(
                          Fragment,
                          null,
                          renderList($props.data?.[source].errors, (error) => {
                            return openBlock(), createElementBlock(
                              "div",
                              {
                                class: normalizeClass([[`val-error-type-${error.type}`, `val-error-source-${source}`], "alert alert-danger val val-error"]),
                                role: "alert"
                              },
                              [
                                error.type === "unknown-parent" ? (openBlock(), createElementBlock(
                                  Fragment,
                                  { key: 0 },
                                  [
                                    createVNode($setup["Diagnostic"], { diagnostic: error }, {
                                      default: withCtx(() => [
                                        createVNode($setup["ErrorLink"], {
                                          error,
                                          short_repository_name: $setup.shortRepoName,
                                          term: error.term ?? error.relation
                                        }, null, 8, ["error", "short_repository_name", "term"])
                                      ]),
                                      _: 2
                                      /* DYNAMIC */
                                    }, 1032, ["diagnostic"]),
                                    $props.release.release_script.short_repository_name.toLowerCase() !== "addicto" ? (openBlock(), createElementBlock("button", {
                                      key: 0,
                                      class: normalizeClass([{ "btn-success": $setup.autoFixState(error) === "fixed", "btn-danger": $setup.autoFixState(error) === "impossible" }, "btn btn-primary"]),
                                      onClick: ($event) => $setup.autofix(error)
                                    }, [
                                      $setup.autoFixState(error) === "loading" ? (openBlock(), createElementBlock("i", _hoisted_63)) : createCommentVNode("v-if", true),
                                      $setup.autoFixState(error) === "fixed" ? (openBlock(), createElementBlock("i", _hoisted_73)) : createCommentVNode("v-if", true),
                                      $setup.autoFixState(error) === "impossible" ? (openBlock(), createElementBlock("i", _hoisted_83)) : createCommentVNode("v-if", true),
                                      _cache[4] || (_cache[4] = createTextVNode(" Try auto fix "))
                                    ], 10, _hoisted_53)) : createCommentVNode("v-if", true)
                                  ],
                                  64
                                  /* STABLE_FRAGMENT */
                                )) : error.type === "missing-parent" ? (openBlock(), createBlock($setup["Diagnostic"], {
                                  key: 1,
                                  diagnostic: error
                                }, {
                                  default: withCtx(() => [
                                    createVNode($setup["ErrorLink"], {
                                      error,
                                      short_repository_name: $setup.shortRepoName,
                                      term: error.term ?? error.relation
                                    }, null, 8, ["error", "short_repository_name", "term"])
                                  ]),
                                  _: 2
                                  /* DYNAMIC */
                                }, 1032, ["diagnostic"])) : error.type === "no-parent" ? (openBlock(), createBlock($setup["Diagnostic"], {
                                  key: 2,
                                  diagnostic: error
                                }, {
                                  default: withCtx(() => [
                                    createVNode($setup["ErrorLink"], {
                                      error,
                                      short_repository_name: $setup.shortRepoName,
                                      term: error.term ?? error.relation
                                    }, null, 8, ["error", "short_repository_name", "term"])
                                  ]),
                                  _: 2
                                  /* DYNAMIC */
                                }, 1032, ["diagnostic"])) : error.type === "ignored-parent" ? (openBlock(), createBlock($setup["Diagnostic"], {
                                  key: 3,
                                  diagnostic: error
                                }, {
                                  default: withCtx(() => [
                                    createVNode($setup["ErrorLink"], {
                                      error,
                                      short_repository_name: $setup.shortRepoName,
                                      term: error.term ?? error.relation
                                    }, null, 8, ["error", "short_repository_name", "term"])
                                  ]),
                                  _: 2
                                  /* DYNAMIC */
                                }, 1032, ["diagnostic"])) : error.type === "missing-label" ? (openBlock(), createBlock($setup["Diagnostic"], {
                                  key: 4,
                                  diagnostic: error
                                }, {
                                  default: withCtx(() => [
                                    createVNode($setup["ErrorLink"], {
                                      error,
                                      short_repository_name: $setup.shortRepoName,
                                      term: error.term ?? error.relation
                                    }, null, 8, ["error", "short_repository_name", "term"])
                                  ]),
                                  _: 2
                                  /* DYNAMIC */
                                }, 1032, ["diagnostic"])) : error.type === "missing-id" ? (openBlock(), createBlock($setup["Diagnostic"], {
                                  key: 5,
                                  diagnostic: error
                                }, {
                                  default: withCtx(() => [
                                    createVNode($setup["ErrorLink"], {
                                      error,
                                      short_repository_name: $setup.shortRepoName,
                                      term: error.term ?? error.relation
                                    }, null, 8, ["error", "short_repository_name", "term"])
                                  ]),
                                  _: 2
                                  /* DYNAMIC */
                                }, 1032, ["diagnostic"])) : error.type === "unknown-disjoint" ? (openBlock(), createBlock($setup["Diagnostic"], {
                                  key: 6,
                                  diagnostic: error
                                }, {
                                  default: withCtx(() => [
                                    createVNode($setup["ErrorLink"], {
                                      error,
                                      short_repository_name: $setup.shortRepoName,
                                      term: error.term ?? error.relation
                                    }, null, 8, ["error", "short_repository_name", "term"])
                                  ]),
                                  _: 2
                                  /* DYNAMIC */
                                }, 1032, ["diagnostic"])) : error.type === "unknown-relation-value" ? (openBlock(), createBlock($setup["Diagnostic"], {
                                  key: 7,
                                  diagnostic: error
                                }, {
                                  default: withCtx(() => [
                                    createVNode($setup["ErrorLink"], {
                                      error,
                                      short_repository_name: $setup.shortRepoName,
                                      term: error.term ?? error.relation
                                    }, null, 8, ["error", "short_repository_name", "term"])
                                  ]),
                                  _: 2
                                  /* DYNAMIC */
                                }, 1032, ["diagnostic"])) : error.type === "ignored-relation-value" ? (openBlock(), createBlock($setup["Diagnostic"], {
                                  key: 8,
                                  diagnostic: error
                                }, {
                                  default: withCtx(() => [
                                    createVNode($setup["ErrorLink"], {
                                      error,
                                      short_repository_name: $setup.shortRepoName,
                                      term: error.term ?? error.relation
                                    }, null, 8, ["error", "short_repository_name", "term"])
                                  ]),
                                  _: 2
                                  /* DYNAMIC */
                                }, 1032, ["diagnostic"])) : error.type === "unknown-range" ? (openBlock(), createBlock($setup["Diagnostic"], {
                                  key: 9,
                                  diagnostic: error
                                }, {
                                  default: withCtx(() => [
                                    createVNode($setup["ErrorLink"], {
                                      error,
                                      short_repository_name: $setup.shortRepoName,
                                      term: error.relation
                                    }, null, 8, ["error", "short_repository_name", "term"])
                                  ]),
                                  _: 2
                                  /* DYNAMIC */
                                }, 1032, ["diagnostic"])) : error.type === "unknown-domain" ? (openBlock(), createBlock($setup["Diagnostic"], {
                                  key: 10,
                                  diagnostic: error
                                }, {
                                  default: withCtx(() => [
                                    createVNode($setup["ErrorLink"], {
                                      error,
                                      short_repository_name: $setup.shortRepoName,
                                      term: error.relation
                                    }, null, 8, ["error", "short_repository_name", "term"])
                                  ]),
                                  _: 2
                                  /* DYNAMIC */
                                }, 1032, ["diagnostic"])) : error.type === "unknown-relation" ? (openBlock(), createBlock($setup["Diagnostic"], {
                                  key: 11,
                                  diagnostic: error
                                }, {
                                  default: withCtx(() => [
                                    createVNode($setup["ErrorLink"], {
                                      error,
                                      short_repository_name: $setup.shortRepoName,
                                      term: error.relation
                                    }, null, 8, ["error", "short_repository_name", "term"])
                                  ]),
                                  _: 2
                                  /* DYNAMIC */
                                }, 1032, ["diagnostic"])) : error.type === "duplicate" ? (openBlock(), createElementBlock(
                                  Fragment,
                                  { key: 12 },
                                  [
                                    _cache[11] || (_cache[11] = createBaseVNode(
                                      "h5",
                                      null,
                                      "Conflicting entries (duplicates)",
                                      -1
                                      /* HOISTED */
                                    )),
                                    createBaseVNode("p", null, [
                                      createTextVNode(
                                        " There are multiple terms for the " + toDisplayString(error.duplicate_field) + " ",
                                        1
                                        /* TEXT */
                                      ),
                                      createBaseVNode(
                                        "code",
                                        null,
                                        toDisplayString(error.duplicate_value),
                                        1
                                        /* TEXT */
                                      ),
                                      _cache[5] || (_cache[5] = createTextVNode(": "))
                                    ]),
                                    createBaseVNode("ul", null, [
                                      (openBlock(true), createElementBlock(
                                        Fragment,
                                        null,
                                        renderList(error.mismatches, (mismatch) => {
                                          return openBlock(), createElementBlock("li", null, [
                                            createBaseVNode("p", null, [
                                              createBaseVNode(
                                                "span",
                                                _hoisted_93,
                                                toDisplayString(mismatch.field),
                                                1
                                                /* TEXT */
                                              ),
                                              _cache[6] || (_cache[6] = createTextVNode(" is ")),
                                              ["definition", "curation status"].indexOf(mismatch.field) >= 0 ? (openBlock(), createElementBlock(
                                                "code",
                                                _hoisted_103,
                                                toDisplayString(mismatch.a.relations.find((x) => x[0]?.label?.endsWith(mismatch.field))?.[1]),
                                                1
                                                /* TEXT */
                                              )) : (openBlock(), createElementBlock(
                                                "code",
                                                _hoisted_114,
                                                toDisplayString(mismatch.a[mismatch.field]),
                                                1
                                                /* TEXT */
                                              )),
                                              _cache[7] || (_cache[7] = createBaseVNode(
                                                "br",
                                                null,
                                                null,
                                                -1
                                                /* HOISTED */
                                              )),
                                              createVNode($setup["ErrorLink"], {
                                                short_repository_name: $setup.shortRepoName,
                                                term: mismatch.a
                                              }, null, 8, ["short_repository_name", "term"]),
                                              _cache[8] || (_cache[8] = createBaseVNode(
                                                "br",
                                                null,
                                                null,
                                                -1
                                                /* HOISTED */
                                              )),
                                              _cache[9] || (_cache[9] = createTextVNode(" and ")),
                                              ["definition", "curation status"].indexOf(mismatch.field) >= 0 ? (openBlock(), createElementBlock(
                                                "code",
                                                _hoisted_123,
                                                toDisplayString(mismatch.b.relations.find((x) => x[0]?.label?.endsWith(mismatch.field))?.[1]),
                                                1
                                                /* TEXT */
                                              )) : (openBlock(), createElementBlock(
                                                "code",
                                                _hoisted_133,
                                                toDisplayString(mismatch.b[mismatch.field]),
                                                1
                                                /* TEXT */
                                              )),
                                              _cache[10] || (_cache[10] = createBaseVNode(
                                                "br",
                                                null,
                                                null,
                                                -1
                                                /* HOISTED */
                                              )),
                                              createVNode($setup["ErrorLink"], {
                                                short_repository_name: $setup.shortRepoName,
                                                term: mismatch.b
                                              }, null, 8, ["short_repository_name", "term"])
                                            ])
                                          ]);
                                        }),
                                        256
                                        /* UNKEYED_FRAGMENT */
                                      ))
                                    ])
                                  ],
                                  64
                                  /* STABLE_FRAGMENT */
                                )) : (openBlock(), createElementBlock(
                                  Fragment,
                                  { key: 13 },
                                  [
                                    createBaseVNode(
                                      "h5",
                                      null,
                                      toDisplayString(error.type.replace("-", " ")),
                                      1
                                      /* TEXT */
                                    ),
                                    createBaseVNode("p", null, [
                                      createTextVNode(
                                        toDisplayString(error.msg),
                                        1
                                        /* TEXT */
                                      ),
                                      _cache[12] || (_cache[12] = createBaseVNode(
                                        "br",
                                        null,
                                        null,
                                        -1
                                        /* HOISTED */
                                      )),
                                      createVNode($setup["ErrorLink"], {
                                        error,
                                        short_repository_name: $setup.shortRepoName
                                      }, null, 8, ["error", "short_repository_name"])
                                    ]),
                                    createBaseVNode(
                                      "pre",
                                      null,
                                      toDisplayString(JSON.stringify(error, void 0, 2)),
                                      1
                                      /* TEXT */
                                    )
                                  ],
                                  64
                                  /* STABLE_FRAGMENT */
                                ))
                              ],
                              2
                              /* CLASS */
                            );
                          }),
                          256
                          /* UNKEYED_FRAGMENT */
                        )),
                        (openBlock(true), createElementBlock(
                          Fragment,
                          null,
                          renderList($props.data?.[source].warnings, (warning) => {
                            return openBlock(), createElementBlock("div", _hoisted_143, [
                              warning.type == "incomplete-term" ? (openBlock(), createBlock($setup["Diagnostic"], {
                                key: 0,
                                diagnostic: warning
                              }, {
                                default: withCtx(() => [
                                  createVNode($setup["ErrorLink"], {
                                    error: warning,
                                    short_repository_name: $setup.shortRepoName
                                  }, null, 8, ["error", "short_repository_name"])
                                ]),
                                _: 2
                                /* DYNAMIC */
                              }, 1032, ["diagnostic"])) : warning.type === "unknown-column" ? (openBlock(), createBlock($setup["Diagnostic"], {
                                key: 1,
                                diagnostic: warning
                              }, null, 8, ["diagnostic"])) : warning.type === "missing-import" ? (openBlock(), createElementBlock(
                                Fragment,
                                { key: 2 },
                                [
                                  createVNode($setup["Diagnostic"], { diagnostic: warning }, {
                                    default: withCtx(() => [
                                      createVNode($setup["ErrorLink"], {
                                        error: warning,
                                        short_repository_name: $setup.shortRepoName,
                                        term: warning.term
                                      }, null, 8, ["error", "short_repository_name", "term"])
                                    ]),
                                    _: 2
                                    /* DYNAMIC */
                                  }, 1032, ["diagnostic"]),
                                  createBaseVNode("button", {
                                    class: normalizeClass([{ "btn-success": $setup.autoFixState(warning) === "fixed", "btn-danger": $setup.autoFixState(warning) === "impossible" }, "btn btn-primary"]),
                                    onClick: ($event) => $setup.autofix(warning)
                                  }, [
                                    $setup.autoFixState(warning) === "loading" ? (openBlock(), createElementBlock("i", _hoisted_162)) : createCommentVNode("v-if", true),
                                    $setup.autoFixState(warning) === "fixed" ? (openBlock(), createElementBlock("i", _hoisted_172)) : createCommentVNode("v-if", true),
                                    $setup.autoFixState(warning) === "impossible" ? (openBlock(), createElementBlock("i", _hoisted_182)) : createCommentVNode("v-if", true),
                                    _cache[13] || (_cache[13] = createTextVNode(" Import "))
                                  ], 10, _hoisted_152)
                                ],
                                64
                                /* STABLE_FRAGMENT */
                              )) : warning.type === "inconsistent-import" ? (openBlock(), createElementBlock(
                                Fragment,
                                { key: 3 },
                                [
                                  createVNode($setup["Diagnostic"], { diagnostic: warning }, {
                                    default: withCtx(() => [
                                      createVNode($setup["ErrorLink"], {
                                        error: warning,
                                        short_repository_name: $setup.shortRepoName,
                                        term: warning.term
                                      }, null, 8, ["error", "short_repository_name", "term"])
                                    ]),
                                    _: 2
                                    /* DYNAMIC */
                                  }, 1032, ["diagnostic"]),
                                  createBaseVNode("button", {
                                    class: normalizeClass([{ "btn-success": $setup.autoFixState(warning) === "fixed", "btn-danger": $setup.autoFixState(warning) === "impossible" }, "btn btn-primary"]),
                                    onClick: ($event) => $setup.autofixUpdateTerm(warning, warning.term.id, {
                                      ...warning.term.id,
                                      label: warning.term.label,
                                      id: warning.term.id
                                    })
                                  }, [
                                    $setup.autoFixState(warning) === "loading" ? (openBlock(), createElementBlock("i", _hoisted_202)) : createCommentVNode("v-if", true),
                                    $setup.autoFixState(warning) === "fixed" ? (openBlock(), createElementBlock("i", _hoisted_213)) : createCommentVNode("v-if", true),
                                    $setup.autoFixState(warning) === "impossible" ? (openBlock(), createElementBlock("i", _hoisted_223)) : createCommentVNode("v-if", true),
                                    _cache[16] || (_cache[16] = createTextVNode(" Change ")),
                                    warning.term.id !== warning.imported_term.id ? (openBlock(), createElementBlock(
                                      Fragment,
                                      { key: 3 },
                                      [
                                        _cache[14] || (_cache[14] = createTextVNode(" ID to ")),
                                        createBaseVNode(
                                          "code",
                                          null,
                                          toDisplayString(warning.imported_term.id),
                                          1
                                          /* TEXT */
                                        )
                                      ],
                                      64
                                      /* STABLE_FRAGMENT */
                                    )) : (openBlock(), createElementBlock(
                                      Fragment,
                                      { key: 4 },
                                      [
                                        _cache[15] || (_cache[15] = createTextVNode("label to ")),
                                        createBaseVNode(
                                          "code",
                                          null,
                                          toDisplayString(warning.imported_term.label),
                                          1
                                          /* TEXT */
                                        )
                                      ],
                                      64
                                      /* STABLE_FRAGMENT */
                                    ))
                                  ], 10, _hoisted_192)
                                ],
                                64
                                /* STABLE_FRAGMENT */
                              )) : (openBlock(), createElementBlock(
                                Fragment,
                                { key: 4 },
                                [
                                  createBaseVNode(
                                    "h5",
                                    null,
                                    toDisplayString(warning.type.replace("-", " ")),
                                    1
                                    /* TEXT */
                                  ),
                                  createBaseVNode("p", null, [
                                    createTextVNode(
                                      toDisplayString(warning.msg),
                                      1
                                      /* TEXT */
                                    ),
                                    _cache[17] || (_cache[17] = createBaseVNode(
                                      "br",
                                      null,
                                      null,
                                      -1
                                      /* HOISTED */
                                    )),
                                    createVNode($setup["ErrorLink"], {
                                      error: warning,
                                      short_repository_name: $setup.shortRepoName
                                    }, null, 8, ["error", "short_repository_name"])
                                  ]),
                                  createBaseVNode(
                                    "pre",
                                    null,
                                    toDisplayString(JSON.stringify(warning, void 0, 2)),
                                    1
                                    /* TEXT */
                                  )
                                ],
                                64
                                /* STABLE_FRAGMENT */
                              ))
                            ]);
                          }),
                          256
                          /* UNKEYED_FRAGMENT */
                        ))
                      ],
                      64
                      /* STABLE_FRAGMENT */
                    )) : createCommentVNode("v-if", true)
                  ],
                  64
                  /* STABLE_FRAGMENT */
                );
              }),
              256
              /* UNKEYED_FRAGMENT */
            ))
          ],
          64
          /* STABLE_FRAGMENT */
        ))
      ],
      64
      /* STABLE_FRAGMENT */
    );
  }

  // js/release/steps/Validation.vue
  Validation_default.render = render8;
  Validation_default.__file = "js/release/steps/Validation.vue";
  var Validation_default2 = Validation_default;

  // sfc-script:/home/bjoern/development/onto-spread-ed/js/release/steps/HumanVerification.vue?type=script
  var HumanVerification_default = /* @__PURE__ */ defineComponent({
    __name: "HumanVerification",
    props: {
      data: { type: Object, required: false },
      release: { type: null, required: true },
      selectedSubStep: { type: [String, null], required: true }
    },
    emits: ["release-control"],
    setup(__props, { expose: __expose }) {
      __expose();
      const props = __props;
      const checkHierarchy = ref(props.release.state === "completed");
      const checkLabels = ref(props.release.state === "completed");
      const checkHierarchicalSpreadsheets = ref(props.release.state === "completed");
      const hasHierarchicalSpreadsheets = computed2(() => !!props.data?.files?.find((x) => x.name.endsWith(".xlsx")));
      const allChecked = computed2(() => [
        checkLabels.value,
        checkHierarchy.value,
        !hasHierarchicalSpreadsheets.value || checkHierarchicalSpreadsheets.value
      ].reduce((p2, v) => p2 && v, true));
      const __returned__ = { props, checkHierarchy, checkLabels, checkHierarchicalSpreadsheets, hasHierarchicalSpreadsheets, allChecked };
      Object.defineProperty(__returned__, "__isScriptSetup", { enumerable: false, value: true });
      return __returned__;
    }
  });

  // sfc-template:/home/bjoern/development/onto-spread-ed/js/release/steps/HumanVerification.vue?type=template
  var _hoisted_115 = ["href", "download"];
  var _hoisted_214 = { class: "list-unstyled" };
  var _hoisted_38 = { class: "ms-4" };
  var _hoisted_46 = { class: "form-check" };
  var _hoisted_54 = ["disabled"];
  var _hoisted_64 = { class: "ms-4" };
  var _hoisted_74 = { class: "form-check" };
  var _hoisted_84 = ["disabled"];
  var _hoisted_94 = {
    key: 0,
    class: "ms-4"
  };
  var _hoisted_104 = { class: "form-check" };
  var _hoisted_116 = ["disabled"];
  var _hoisted_124 = ["disabled"];
  function render9(_ctx, _cache, $props, $setup, $data, $options) {
    return openBlock(), createElementBlock(
      Fragment,
      null,
      [
        _cache[7] || (_cache[7] = createBaseVNode(
          "h3",
          null,
          "Verify the built ontologies",
          -1
          /* HOISTED */
        )),
        _cache[8] || (_cache[8] = createBaseVNode(
          "p",
          null,
          [
            createTextVNode(" Please download the built files and ontologies and open them in Prot\xE9g\xE9 (download "),
            createBaseVNode("a", { href: "https://protege.stanford.edu/software.php#desktop-protege" }, "here"),
            createTextVNode(" or use "),
            createBaseVNode("a", { href: "https://webprotege.stanford.edu/" }, "Web protege"),
            createTextVNode("). ")
          ],
          -1
          /* HOISTED */
        )),
        createBaseVNode("ul", null, [
          (openBlock(true), createElementBlock(
            Fragment,
            null,
            renderList($props.data?.files, (file) => {
              return openBlock(), createElementBlock("li", null, [
                createBaseVNode("a", {
                  href: file.link,
                  download: file.name
                }, toDisplayString(file.name), 9, _hoisted_115)
              ]);
            }),
            256
            /* UNKEYED_FRAGMENT */
          ))
        ]),
        _cache[9] || (_cache[9] = createBaseVNode(
          "p",
          null,
          " Check the following things: ",
          -1
          /* HOISTED */
        )),
        createBaseVNode("ul", _hoisted_214, [
          createBaseVNode("li", _hoisted_38, [
            createBaseVNode("div", _hoisted_46, [
              withDirectives(createBaseVNode("input", {
                "onUpdate:modelValue": _cache[0] || (_cache[0] = ($event) => $setup.checkHierarchy = $event),
                disabled: $props.release.state !== "waiting-for-user",
                class: "form-check-input checklist",
                type: "checkbox",
                value: "",
                id: "chk-inferred"
              }, null, 8, _hoisted_54), [
                [vModelCheckbox, $setup.checkHierarchy]
              ]),
              _cache[4] || (_cache[4] = createBaseVNode(
                "label",
                {
                  class: "form-check-label",
                  for: "chk-inferred"
                },
                " Start the reasoner. Does the inferred hierarchy look alright? ",
                -1
                /* HOISTED */
              ))
            ])
          ]),
          createBaseVNode("li", _hoisted_64, [
            createBaseVNode("div", _hoisted_74, [
              withDirectives(createBaseVNode("input", {
                "onUpdate:modelValue": _cache[1] || (_cache[1] = ($event) => $setup.checkLabels = $event),
                disabled: $props.release.state !== "waiting-for-user",
                class: "form-check-input checklist",
                type: "checkbox",
                value: "",
                id: "chk-labels"
              }, null, 8, _hoisted_84), [
                [vModelCheckbox, $setup.checkLabels]
              ]),
              _cache[5] || (_cache[5] = createBaseVNode(
                "label",
                {
                  class: "form-check-label",
                  for: "chk-labels"
                },
                " Do the labels look alright? ",
                -1
                /* HOISTED */
              ))
            ])
          ]),
          $setup.hasHierarchicalSpreadsheets ? (openBlock(), createElementBlock("li", _hoisted_94, [
            createBaseVNode("div", _hoisted_104, [
              withDirectives(createBaseVNode("input", {
                "onUpdate:modelValue": _cache[2] || (_cache[2] = ($event) => $setup.checkHierarchicalSpreadsheets = $event),
                disabled: $props.release.state !== "waiting-for-user",
                class: "form-check-input checklist",
                type: "checkbox",
                value: "",
                id: "chk-hierarchical-spreadsheets"
              }, null, 8, _hoisted_116), [
                [vModelCheckbox, $setup.checkHierarchicalSpreadsheets]
              ]),
              _cache[6] || (_cache[6] = createBaseVNode(
                "label",
                {
                  class: "form-check-label",
                  for: "chk-hierarchical-spreadsheets"
                },
                " Do the hierarchy, labels, and other fields in the hierarchical spreadsheets look alright? ",
                -1
                /* HOISTED */
              ))
            ])
          ])) : createCommentVNode("v-if", true)
        ]),
        createBaseVNode("button", {
          class: "btn btn-success w-100",
          id: "btn-publish-release",
          disabled: !$setup.allChecked || $props.release.state !== "waiting-for-user",
          onClick: _cache[3] || (_cache[3] = ($event) => _ctx.$emit("release-control", "continue"))
        }, " Everything looks alright. Publish the release! ", 8, _hoisted_124)
      ],
      64
      /* STABLE_FRAGMENT */
    );
  }

  // js/release/steps/HumanVerification.vue
  HumanVerification_default.render = render9;
  HumanVerification_default.__file = "js/release/steps/HumanVerification.vue";
  var HumanVerification_default2 = HumanVerification_default;

  // sfc-script:/home/bjoern/development/onto-spread-ed/js/release/TechnicalError.vue?type=script
  var TechnicalError_default = /* @__PURE__ */ defineComponent({
    __name: "TechnicalError",
    props: {
      release: { type: null, required: true },
      details: { type: Object, required: true }
    },
    setup(__props, { expose: __expose }) {
      __expose();
      const props = __props;
      const __returned__ = { props };
      Object.defineProperty(__returned__, "__isScriptSetup", { enumerable: false, value: true });
      return __returned__;
    }
  });

  // sfc-template:/home/bjoern/development/onto-spread-ed/js/release/TechnicalError.vue?type=template
  var _hoisted_117 = { class: "alert alert-danger" };
  var _hoisted_215 = { key: 1 };
  function render10(_ctx, _cache, $props, $setup, $data, $options) {
    return openBlock(), createElementBlock(
      Fragment,
      null,
      [
        _cache[4] || (_cache[4] = createBaseVNode(
          "div",
          { class: "alert alert-danger" },
          [
            createBaseVNode("h4", null, "An error occurred while building the file"),
            createBaseVNode("p", null, " A technical error occurred. Please contact an administrator. ")
          ],
          -1
          /* HOISTED */
        )),
        (openBlock(true), createElementBlock(
          Fragment,
          null,
          renderList($props.details.errors, (error) => {
            return openBlock(), createElementBlock("div", _hoisted_117, [
              "code" in error ? (openBlock(), createElementBlock(
                Fragment,
                { key: 0 },
                [
                  _cache[0] || (_cache[0] = createBaseVNode(
                    "h6",
                    null,
                    "Command",
                    -1
                    /* HOISTED */
                  )),
                  createBaseVNode(
                    "pre",
                    null,
                    toDisplayString(error.command),
                    1
                    /* TEXT */
                  ),
                  _cache[1] || (_cache[1] = createBaseVNode(
                    "h6",
                    null,
                    "Return code",
                    -1
                    /* HOISTED */
                  )),
                  createBaseVNode(
                    "p",
                    null,
                    toDisplayString(error.code),
                    1
                    /* TEXT */
                  ),
                  _cache[2] || (_cache[2] = createBaseVNode(
                    "h6",
                    null,
                    "Standard out",
                    -1
                    /* HOISTED */
                  )),
                  createBaseVNode(
                    "pre",
                    null,
                    toDisplayString(error.out),
                    1
                    /* TEXT */
                  ),
                  _cache[3] || (_cache[3] = createBaseVNode(
                    "h6",
                    null,
                    "Standard error",
                    -1
                    /* HOISTED */
                  )),
                  createBaseVNode(
                    "pre",
                    null,
                    toDisplayString(error.err),
                    1
                    /* TEXT */
                  )
                ],
                64
                /* STABLE_FRAGMENT */
              )) : (openBlock(), createElementBlock(
                "pre",
                _hoisted_215,
                toDisplayString(JSON.stringify(error, void 0, 2)),
                1
                /* TEXT */
              ))
            ]);
          }),
          256
          /* UNKEYED_FRAGMENT */
        ))
      ],
      64
      /* STABLE_FRAGMENT */
    );
  }

  // js/release/TechnicalError.vue
  TechnicalError_default.render = render10;
  TechnicalError_default.__file = "js/release/TechnicalError.vue";
  var TechnicalError_default2 = TechnicalError_default;

  // sfc-script:/home/bjoern/development/onto-spread-ed/js/release/steps/GithubPublish.vue?type=script
  var GithubPublish_default = /* @__PURE__ */ defineComponent({
    __name: "GithubPublish",
    props: {
      data: { type: null, required: true },
      release: { type: null, required: true },
      selectedSubStep: { type: [String, null], required: true }
    },
    emits: ["release-control"],
    setup(__props, { expose: __expose }) {
      __expose();
      const __returned__ = { TechnicalError: TechnicalError_default2, ProgressIndicator: ProgressIndicator_default2 };
      Object.defineProperty(__returned__, "__isScriptSetup", { enumerable: false, value: true });
      return __returned__;
    }
  });

  // sfc-template:/home/bjoern/development/onto-spread-ed/js/release/steps/GithubPublish.vue?type=template
  function render11(_ctx, _cache, $props, $setup, $data, $options) {
    return openBlock(), createElementBlock(
      Fragment,
      null,
      [
        _cache[3] || (_cache[3] = createBaseVNode(
          "h3",
          null,
          "Publishing the release",
          -1
          /* HOISTED */
        )),
        $props.release.state == "waiting-for-user" && $props.data && ($props.data.errors?.length ?? 0) > 0 ? (openBlock(), createBlock($setup["TechnicalError"], {
          key: 0,
          release: $props.release,
          details: $props.data
        }, null, 8, ["release", "details"])) : $props.release.state === "completed" ? (openBlock(), createElementBlock(
          Fragment,
          { key: 1 },
          [
            _cache[0] || (_cache[0] = createBaseVNode(
              "p",
              null,
              " The ontologies are now published to github and the release is completed. ",
              -1
              /* HOISTED */
            )),
            _cache[1] || (_cache[1] = createBaseVNode(
              "div",
              {
                class: "text-center w-100 text-success",
                style: { "font-size": "100px" }
              },
              [
                createBaseVNode("i", { class: "fa fa-check-double" })
              ],
              -1
              /* HOISTED */
            ))
          ],
          64
          /* STABLE_FRAGMENT */
        )) : (openBlock(), createBlock($setup["ProgressIndicator"], {
          key: 2,
          details: $props.data,
          release: $props.release
        }, {
          default: withCtx(() => _cache[2] || (_cache[2] = [
            createTextVNode(" The ontologies are being published to github. ")
          ])),
          _: 1
          /* STABLE */
        }, 8, ["details", "release"]))
      ],
      64
      /* STABLE_FRAGMENT */
    );
  }

  // js/release/steps/GithubPublish.vue
  GithubPublish_default.render = render11;
  GithubPublish_default.__file = "js/release/steps/GithubPublish.vue";
  var GithubPublish_default2 = GithubPublish_default;

  // sfc-script:/home/bjoern/development/onto-spread-ed/js/release/steps/BCIOSearch.vue?type=script
  var BCIOSearch_default = /* @__PURE__ */ defineComponent({
    __name: "BCIOSearch",
    props: {
      data: { type: null, required: true },
      release: { type: null, required: true },
      selectedSubStep: { type: [String, null], required: true }
    },
    emits: ["release-control"],
    setup(__props, { expose: __expose }) {
      __expose();
      const __returned__ = { ProgressIndicator: ProgressIndicator_default2 };
      Object.defineProperty(__returned__, "__isScriptSetup", { enumerable: false, value: true });
      return __returned__;
    }
  });

  // sfc-template:/home/bjoern/development/onto-spread-ed/js/release/steps/BCIOSearch.vue?type=template
  var _hoisted_118 = { class: "alert alert-danger" };
  var _hoisted_216 = { key: 1 };
  var _hoisted_39 = { key: 2 };
  function render12(_ctx, _cache, $props, $setup, $data, $options) {
    return openBlock(), createElementBlock(
      Fragment,
      null,
      [
        _cache[1] || (_cache[1] = createBaseVNode(
          "h3",
          null,
          "Publishing the release",
          -1
          /* HOISTED */
        )),
        $props.release.state === "waiting-for-user" && $props.data?.errors?.length > 0 ? (openBlock(true), createElementBlock(
          Fragment,
          { key: 0 },
          renderList($props.data.errors, (error) => {
            return openBlock(), createElementBlock("div", _hoisted_118, [
              error.details && error?.response?.["hydra:description"] ? (openBlock(), createElementBlock(
                Fragment,
                { key: 0 },
                [
                  createBaseVNode(
                    "h4",
                    null,
                    toDisplayString(error.response["hydra:title"]),
                    1
                    /* TEXT */
                  ),
                  createBaseVNode(
                    "p",
                    null,
                    toDisplayString(error.details),
                    1
                    /* TEXT */
                  ),
                  createBaseVNode(
                    "p",
                    null,
                    toDisplayString(error.response["hydra:description"]),
                    1
                    /* TEXT */
                  )
                ],
                64
                /* STABLE_FRAGMENT */
              )) : (openBlock(), createElementBlock(
                "pre",
                _hoisted_216,
                toDisplayString(JSON.stringify(error, void 0, 2)),
                1
                /* TEXT */
              ))
            ]);
          }),
          256
          /* UNKEYED_FRAGMENT */
        )) : (openBlock(), createBlock($setup["ProgressIndicator"], {
          key: 1,
          details: $props.data,
          release: $props.release
        }, {
          default: withCtx(() => _cache[0] || (_cache[0] = [
            createBaseVNode(
              "p",
              null,
              [
                createTextVNode(" The ontologies are being published to BCIOSearch. This will take a while."),
                createBaseVNode("br")
              ],
              -1
              /* HOISTED */
            )
          ])),
          _: 1
          /* STABLE */
        }, 8, ["details", "release"])),
        $props.release.state === "completed" ? (openBlock(), createElementBlock("p", _hoisted_39, " The ontologies were published to BCIOSearch. ")) : createCommentVNode("v-if", true)
      ],
      64
      /* STABLE_FRAGMENT */
    );
  }

  // js/release/steps/BCIOSearch.vue
  BCIOSearch_default.render = render12;
  BCIOSearch_default.__file = "js/release/steps/BCIOSearch.vue";
  var BCIOSearch_default2 = BCIOSearch_default;

  // sfc-script:/home/bjoern/development/onto-spread-ed/js/release/steps/Generic.vue?type=script
  var Generic_default = /* @__PURE__ */ defineComponent({
    __name: "Generic",
    props: {
      data: { type: null, required: true },
      release: { type: null, required: true },
      step: { type: Object, required: true }
    },
    emits: ["release-control"],
    setup(__props, { expose: __expose }) {
      __expose();
      const STEPS = {
        PREPARATION: {
          title: "Preparation",
          running_text: "Excel files are downloaded to the server and prepared.",
          finished_text: "Excel files were downloaded to the server."
        },
        IMPORT_EXTERNAL: {
          title: "Building external dependencies",
          running_text: "External ontologies are now downloaded and converted. This might take a few minutes.",
          finished_text: "External ontologies were successfully downloaded and converted."
        },
        BUILD: {
          title: "Building OWL files",
          running_text: "OWL files are now build.",
          finished_text: "OWL files were successfully built."
        },
        MERGE: {
          title: "Merging files",
          running_text: "Multiple OWL files are being combined into one.",
          finished_text: "Multiple OWL files were combined into one."
        }
      };
      const props = __props;
      function titleCase(str) {
        return str.replace("_", " ").replace(
          /\w\S*/g,
          (text) => text.charAt(0).toUpperCase() + text.substring(1).toLowerCase()
        );
      }
      const title = computed2(() => STEPS[props.step.name]?.title ?? titleCase(props.step.name ?? "<MISSING>"));
      const running_text = computed2(() => STEPS[props.step.name]?.running_text ?? "");
      const finished_text = computed2(() => STEPS[props.step.name]?.finished_text ?? "");
      const __returned__ = { STEPS, props, titleCase, title, running_text, finished_text, TechnicalError: TechnicalError_default2, ProgressIndicator: ProgressIndicator_default2 };
      Object.defineProperty(__returned__, "__isScriptSetup", { enumerable: false, value: true });
      return __returned__;
    }
  });

  // sfc-template:/home/bjoern/development/onto-spread-ed/js/release/steps/Generic.vue?type=template
  var _hoisted_119 = { key: 2 };
  function render13(_ctx, _cache, $props, $setup, $data, $options) {
    return openBlock(), createElementBlock(
      Fragment,
      null,
      [
        createBaseVNode(
          "h3",
          null,
          toDisplayString($setup.title),
          1
          /* TEXT */
        ),
        $props.release.state == "waiting-for-user" && $props.data && ($props.data.errors?.length ?? 0) > 0 ? (openBlock(), createBlock($setup["TechnicalError"], {
          key: 0,
          release: $props.release,
          details: $props.data
        }, null, 8, ["release", "details"])) : (openBlock(), createBlock($setup["ProgressIndicator"], {
          key: 1,
          details: $props.data,
          release: $props.release
        }, {
          default: withCtx(() => [
            createTextVNode(
              toDisplayString($setup.running_text),
              1
              /* TEXT */
            )
          ]),
          _: 1
          /* STABLE */
        }, 8, ["details", "release"])),
        $props.release.state === "completed" ? (openBlock(), createElementBlock(
          "p",
          _hoisted_119,
          toDisplayString($setup.finished_text),
          1
          /* TEXT */
        )) : createCommentVNode("v-if", true)
      ],
      64
      /* STABLE_FRAGMENT */
    );
  }

  // js/release/steps/Generic.vue
  Generic_default.render = render13;
  Generic_default.__file = "js/release/steps/Generic.vue";
  var Generic_default2 = Generic_default;

  // sfc-script:/home/bjoern/development/onto-spread-ed/js/release/Release.vue?type=script
  var Release_default = /* @__PURE__ */ defineComponent({
    __name: "Release",
    setup(__props, { expose: __expose }) {
      __expose();
      const repo = SERVER_DATA.repo;
      const prefix_url2 = URLS.prefix;
      const release = ref(null);
      const loading = ref(false);
      const error = ref(null);
      const selected_step = ref(null);
      const selected_sub_step = ref(null);
      const _steps = {
        "VALIDATION": Validation_default2,
        "HUMAN_VERIFICATION": HumanVerification_default2,
        "GITHUB_PUBLISH": GithubPublish_default2,
        "BCIO_SEARCH": BCIOSearch_default2,
        "ADDICTO_VOCAB": AddictOVocab_default2
      };
      const currentStep = computed2(() => release.value?.release_script.steps[selected_step.value ?? release.value.step] ?? null);
      const stepComponent = computed2(() => _steps[currentStep.value?.name] ?? Generic_default2);
      const stepProps = computed2(() => {
        const possibleProps = {
          data: details.value,
          release: release.value,
          selectedSubStep: selected_sub_step.value,
          step: currentStep.value
        };
        const component = stepComponent.value;
        if (component) {
          const required = Object.keys(component.props);
          return Object.fromEntries(Object.entries(possibleProps).filter(([k, _]) => required.indexOf(k) >= 0));
        }
        return null;
      });
      const details = computed2(() => release.value?.details[(selected_step.value ?? release.value.step).toString()]);
      function subSteps(data) {
        if (data instanceof Object) {
          const val = data;
          const steps = Object.entries(val).filter(
            ([k, v]) => !k.startsWith("_") && ["warnings", "errors", "infos"].indexOf(k) < 0 && Array.isArray(v?.warnings) && Array.isArray(v?.errors)
          );
          return steps.length > 0 ? Object.fromEntries(steps) : null;
        }
        return null;
      }
      async function poll(withLoading = false) {
        const id = release.value?.id ?? `${repo}/running`;
        loading.value = withLoading;
        try {
          let response = await fetch(`${prefix_url2}/api/release/${id}`);
          if (response.ok) {
            release.value = await response.json();
          } else {
            release.value = null;
          }
        } catch (e) {
        } finally {
          loading.value = false;
        }
      }
      onMounted(async () => {
        const lastPathSegment = window.location.pathname.split("/").slice(-1)[0];
        const releaseId = parseInt(lastPathSegment);
        if (!isNaN(releaseId)) {
          release.value = await _request(() => fetch(`${prefix_url2}/api/release/${releaseId}`)) ?? null;
        } else {
          await poll(true);
        }
      });
      let pollInterval = null;
      function startPolling() {
        if (pollInterval === null) {
          pollInterval = setInterval(poll, 2e3);
        }
      }
      const stopWaitingForReleaseStart = watch2(release, (value, oldValue) => {
        if (oldValue === null && value !== null && pollInterval === null && value.state === "running") {
          stopWaitingForReleaseStart();
          startPolling();
        }
      });
      const icon_classes = computed2(() => {
        switch (release.value?.state) {
          case void 0:
          case null:
            return ["fa-regular", "fa-file", "text-black-50"];
          case "canceled":
            return ["fa-regular", "fa-circle-xmark", "text-danger"];
          case "waiting-for-user":
            return ["fa-solid", "fa-user-clock", "text-warning"];
          case "errored":
            return ["fa-solid", "fa-triangle-exclamation", "text-danger"];
          case "completed":
            return ["fa-regular", "fa-circle-check", "text-success"];
          default:
            return ["fa-spinner", "fa-spin", "text-black-50"];
        }
      });
      async function _request(request, post = null) {
        try {
          loading.value = true;
          const response = await request();
          if (response.ok) {
            const value = await response.json();
            if (post !== null) {
              return await post(value);
            } else {
              return value;
            }
          } else {
            const e = await response.json();
            error.value = e.error;
          }
          loading.value = false;
        } catch (e) {
          if (e instanceof Error) {
            error.value = e.message;
          } else {
            error.value = `An unknown error occurred: ${e}`;
          }
        } finally {
          loading.value = false;
        }
      }
      async function startRelease(releaseScript) {
        const r = await _request(() => fetch(prefix_url2 + "/api/release/start", {
          method: "post",
          body: JSON.stringify(releaseScript),
          headers: {
            "Content-Type": "application/json"
          }
        }));
        if (r) {
          release.value = r;
          window.location.pathname = `${prefix_url2}/admin/release/${r.id}`;
        }
      }
      async function cancelRelease() {
        release.value = await _request(() => fetch(`${prefix_url2}/api/release/${repo}/cancel`, {
          method: "post"
        })) ?? null;
      }
      async function restartRelease() {
        const script = release.value?.release_script;
        if (script) {
          await cancelRelease();
          await startRelease(script);
        }
      }
      function errorsOfStep(step) {
        const details2 = release.value?.details[step.toString()];
        if (details2?.hasOwnProperty("errors") && Array.isArray(details2["errors"])) {
          return details2["errors"].length;
        } else if (Array.isArray(details2)) {
          return details2.map((x) => x["errors"]?.length).reduce((p2, c) => c + p2, 0);
        }
      }
      function warningsOfStep(step) {
        const details2 = release.value?.details[step.toString()];
        if (details2?.hasOwnProperty("warnings") && Array.isArray(details2["warnings"])) {
          return details2["warnings"].length;
        } else if (details2) {
          return Object.values(details2).map((x) => x["warnings"]?.length).reduce((p2, c) => c + p2, 0);
        }
      }
      function stepIconClasses(step) {
        if ((release.value?.step ?? 0) >= step) {
          if (errorsOfStep(step) > 0) {
            return "fa fa-triangle-exclamation text-danger".split(" ");
          } else if (warningsOfStep(step) > 0) {
            return "fa fa-triangle-exclamation text-warning".split(" ");
          } else if (release.value?.step === step && release.value.state !== "completed") {
            return "fa-regular fa-circle text-primary".split(" ");
          } else {
            return "fa-regular fa-check-circle text-success".split(" ");
          }
        } else {
          return "fa-regular fa-clock text-warning".split(" ");
        }
      }
      async function doReleaseControl(type) {
        switch (type) {
          case "continue":
            await fetch(`${prefix_url2}/api/release/${repo}/continue`);
            startPolling();
            break;
          default:
            console.warn(`No such release control type: '${type}'`);
        }
      }
      const __returned__ = { repo, prefix_url: prefix_url2, release, loading, error, selected_step, selected_sub_step, _steps, currentStep, stepComponent, stepProps, details, subSteps, poll, get pollInterval() {
        return pollInterval;
      }, set pollInterval(v) {
        pollInterval = v;
      }, startPolling, stopWaitingForReleaseStart, icon_classes, _request, startRelease, cancelRelease, restartRelease, errorsOfStep, warningsOfStep, stepIconClasses, doReleaseControl, Setup: Setup_default2 };
      Object.defineProperty(__returned__, "__isScriptSetup", { enumerable: false, value: true });
      return __returned__;
    }
  });

  // sfc-style:/home/bjoern/development/onto-spread-ed/js/release/Release.vue?type=style&index=0
  {
    const el = document.createElement("style");
    el.textContent = ".loading[data-v-a1bffc1c] {\n  z-index: 1;\n  background: rgba(0, 0, 0, 0.4);\n  position: fixed;\n  top: 0;\n  left: 0;\n  width: 100vw;\n  height: 100vh;\n  display: grid;\n}\n.loading .inner[data-v-a1bffc1c] {\n  margin: auto;\n  justify-self: center;\n  align-self: center;\n  display: flex;\n  flex-direction: column;\n  text-align: center;\n  gap: 14px;\n}\n.loading .inner .spinner-border[data-v-a1bffc1c] {\n  border-width: 10px;\n}\n#release-core .sidebar .btn[data-v-a1bffc1c] {\n  text-align: start !important;\n}";
    document.head.append(el);
  }

  // sfc-template:/home/bjoern/development/onto-spread-ed/js/release/Release.vue?type=template
  var _hoisted_120 = { class: "release" };
  var _hoisted_217 = { class: "d-flex gap-2 align-items-center" };
  var _hoisted_310 = { id: "lbl-release-title" };
  var _hoisted_47 = {
    key: 0,
    id: "release-info",
    class: "align-self-end mb-2 text-muted"
  };
  var _hoisted_55 = {
    key: 0,
    class: "alert alert-danger"
  };
  var _hoisted_65 = {
    key: 1,
    style: { "display": "grid", "grid-template-columns": "240px 1fr", "grid-gap": "50px" },
    class: "text-start w-100",
    id: "release-core"
  };
  var _hoisted_75 = {
    class: "sidebar border",
    style: { "grid-column": "1" }
  };
  var _hoisted_85 = { class: "list-unstyled ps-2" };
  var _hoisted_95 = { class: "mb-1" };
  var _hoisted_105 = { class: "d-flex align-items-center" };
  var _hoisted_1110 = ["onClick"];
  var _hoisted_125 = { key: 0 };
  var _hoisted_134 = {
    key: 0,
    class: "list-unstyled ms-4"
  };
  var _hoisted_144 = { style: { "display": "flex", "align-items": "center" } };
  var _hoisted_153 = {
    key: 0,
    class: "fa fa-circle-exclamation text-danger"
  };
  var _hoisted_163 = {
    key: 1,
    class: "fa fa-triangle-exclamation text-warning"
  };
  var _hoisted_173 = {
    key: 2,
    class: "fa fa-check-circle text-success"
  };
  var _hoisted_183 = ["onClick"];
  var _hoisted_193 = { key: 0 };
  var _hoisted_203 = {
    class: "main",
    style: { "grid-column": "2" }
  };
  var _hoisted_218 = {
    key: 0,
    class: "alert alert-danger"
  };
  var _hoisted_224 = {
    key: 1,
    class: "alert alert-danger"
  };
  var _hoisted_233 = {
    key: 0,
    class: "loading"
  };
  function render14(_ctx, _cache, $props, $setup, $data, $options) {
    return openBlock(), createElementBlock(
      Fragment,
      null,
      [
        createBaseVNode("div", _hoisted_120, [
          createBaseVNode("div", _hoisted_217, [
            createBaseVNode("h1", _hoisted_310, [
              createBaseVNode(
                "i",
                {
                  id: "icon-release",
                  class: normalizeClass(["fa", $setup.icon_classes])
                },
                null,
                2
                /* CLASS */
              ),
              createTextVNode(
                " Release " + toDisplayString($setup.repo),
                1
                /* TEXT */
              )
            ]),
            $setup.release ? (openBlock(), createElementBlock(
              "span",
              _hoisted_47,
              " started by " + toDisplayString($setup.release.started_by) + " on " + toDisplayString(_ctx.$filters.formatDate($setup.release.start)),
              1
              /* TEXT */
            )) : createCommentVNode("v-if", true),
            _cache[3] || (_cache[3] = createBaseVNode(
              "span",
              { class: "flex-fill" },
              null,
              -1
              /* HOISTED */
            )),
            $setup.release && ["running", "waiting-for-user", "errored"].indexOf($setup.release.state) >= 0 ? (openBlock(), createElementBlock(
              Fragment,
              { key: 1 },
              [
                createBaseVNode("button", {
                  class: "btn btn-warning",
                  id: "btn-release-restart",
                  onClick: $setup.restartRelease
                }, _cache[1] || (_cache[1] = [
                  createBaseVNode(
                    "i",
                    { class: "fa fa-rotate-left" },
                    null,
                    -1
                    /* HOISTED */
                  ),
                  createTextVNode(" Restart ")
                ])),
                createBaseVNode("button", {
                  class: "btn btn-danger",
                  id: "btn-release-cancel",
                  onClick: $setup.cancelRelease
                }, _cache[2] || (_cache[2] = [
                  createBaseVNode(
                    "i",
                    { class: "fa fa-cancel" },
                    null,
                    -1
                    /* HOISTED */
                  ),
                  createTextVNode(" Cancel ")
                ]))
              ],
              64
              /* STABLE_FRAGMENT */
            )) : createCommentVNode("v-if", true)
          ]),
          !$setup.release && !$setup.loading ? (openBlock(), createElementBlock(
            Fragment,
            { key: 0 },
            [
              $setup.error !== null ? (openBlock(), createElementBlock("div", _hoisted_55, [
                _cache[4] || (_cache[4] = createBaseVNode(
                  "h4",
                  null,
                  "An error occurred",
                  -1
                  /* HOISTED */
                )),
                createTextVNode(
                  " " + toDisplayString($setup.error),
                  1
                  /* TEXT */
                )
              ])) : createCommentVNode("v-if", true),
              !$setup.release ? (openBlock(), createBlock($setup["Setup"], {
                key: 1,
                style: { "max-width": "1080px", "margin": "0 auto" },
                repo: $setup.repo,
                onSettingsConfirmed: _cache[0] || (_cache[0] = ($event) => $setup.startRelease($event))
              }, null, 8, ["repo"])) : createCommentVNode("v-if", true)
            ],
            64
            /* STABLE_FRAGMENT */
          )) : createCommentVNode("v-if", true),
          $setup.release !== null ? (openBlock(), createElementBlock("div", _hoisted_65, [
            createBaseVNode("div", _hoisted_75, [
              createBaseVNode("ul", _hoisted_85, [
                (openBlock(true), createElementBlock(
                  Fragment,
                  null,
                  renderList($setup.release.release_script.steps, (step, i) => {
                    return openBlock(), createElementBlock("li", _hoisted_95, [
                      createBaseVNode("div", _hoisted_105, [
                        createBaseVNode(
                          "i",
                          {
                            class: normalizeClass($setup.stepIconClasses(i))
                          },
                          null,
                          2
                          /* CLASS */
                        ),
                        createBaseVNode("a", {
                          class: "btn border-0",
                          onClick: ($event) => {
                            $setup.selected_step = i;
                            $setup.selected_sub_step = null;
                          }
                        }, [
                          ($setup.selected_step !== null ? $setup.selected_step == i : $setup.release.step == i) ? (openBlock(), createElementBlock(
                            "strong",
                            _hoisted_125,
                            toDisplayString(_ctx.$filters.formatText(step.name)),
                            1
                            /* TEXT */
                          )) : (openBlock(), createElementBlock(
                            Fragment,
                            { key: 1 },
                            [
                              createTextVNode(
                                toDisplayString(_ctx.$filters.formatText(step.name)),
                                1
                                /* TEXT */
                              )
                            ],
                            64
                            /* STABLE_FRAGMENT */
                          ))
                        ], 8, _hoisted_1110)
                      ]),
                      $setup.subSteps ? (openBlock(), createElementBlock("ul", _hoisted_134, [
                        (openBlock(true), createElementBlock(
                          Fragment,
                          null,
                          renderList($setup.subSteps($setup.release.details[i]), (val, key) => {
                            return openBlock(), createElementBlock("li", _hoisted_144, [
                              (val.errors?.length ?? 0) > 0 ? (openBlock(), createElementBlock("i", _hoisted_153)) : (val.warnings?.length ?? 0) > 0 ? (openBlock(), createElementBlock("i", _hoisted_163)) : (openBlock(), createElementBlock("i", _hoisted_173)),
                              createBaseVNode("a", {
                                class: "btn border-0 text-truncate",
                                onClick: ($event) => $setup.selected_sub_step = $setup.selected_sub_step === key ? null : key
                              }, [
                                $setup.selected_sub_step === key ? (openBlock(), createElementBlock(
                                  "strong",
                                  _hoisted_193,
                                  toDisplayString(key),
                                  1
                                  /* TEXT */
                                )) : (openBlock(), createElementBlock(
                                  Fragment,
                                  { key: 1 },
                                  [
                                    createTextVNode(
                                      toDisplayString(key),
                                      1
                                      /* TEXT */
                                    )
                                  ],
                                  64
                                  /* STABLE_FRAGMENT */
                                ))
                              ], 8, _hoisted_183)
                            ]);
                          }),
                          256
                          /* UNKEYED_FRAGMENT */
                        ))
                      ])) : createCommentVNode("v-if", true)
                    ]);
                  }),
                  256
                  /* UNKEYED_FRAGMENT */
                ))
              ])
            ]),
            createBaseVNode("div", _hoisted_203, [
              $setup.error !== null ? (openBlock(), createElementBlock("div", _hoisted_218, [
                _cache[5] || (_cache[5] = createBaseVNode(
                  "h4",
                  null,
                  "An error occurred",
                  -1
                  /* HOISTED */
                )),
                createTextVNode(
                  " " + toDisplayString($setup.error),
                  1
                  /* TEXT */
                )
              ])) : createCommentVNode("v-if", true),
              $setup.details?.error ? (openBlock(), createElementBlock("div", _hoisted_224, [
                createBaseVNode(
                  "h4",
                  null,
                  "An error occurred: " + toDisplayString($setup.details.error.short),
                  1
                  /* TEXT */
                ),
                createBaseVNode(
                  "pre",
                  null,
                  toDisplayString($setup.details.error.long),
                  1
                  /* TEXT */
                )
              ])) : createCommentVNode("v-if", true),
              (openBlock(), createBlock(
                resolveDynamicComponent($setup.stepComponent),
                mergeProps($setup.stepProps, { onReleaseControl: $setup.doReleaseControl }),
                null,
                16
                /* FULL_PROPS */
              ))
            ])
          ])) : createCommentVNode("v-if", true)
        ]),
        $setup.loading ? (openBlock(), createElementBlock("div", _hoisted_233, _cache[6] || (_cache[6] = [
          createBaseVNode(
            "div",
            { class: "inner text-light" },
            [
              createBaseVNode("div", {
                class: "spinner-border",
                style: { "width": "5rem", "height": "5rem" },
                role: "status"
              }),
              createBaseVNode("h5", null, "Loading...")
            ],
            -1
            /* HOISTED */
          )
        ]))) : createCommentVNode("v-if", true)
      ],
      64
      /* STABLE_FRAGMENT */
    );
  }

  // js/release/Release.vue
  Release_default.render = render14;
  Release_default.__file = "js/release/Release.vue";
  Release_default.__scopeId = "data-v-a1bffc1c";
  var Release_default2 = Release_default;

  // js/common/filter.ts
  function pluralise(str, listOrAmount) {
    let amount;
    if (Array.isArray(listOrAmount)) {
      amount = listOrAmount.length;
    } else if (listOrAmount) {
      amount = listOrAmount;
    } else {
      amount = 2;
    }
    if (amount < 2) {
      return str;
    }
    if (str?.endsWith("y")) {
      return str.substring(0, str.length - 1) + "ies";
    }
    if (str) {
      return str + "s";
    }
    return str;
  }
  function formatText(str) {
    const s = str.trim().toLowerCase().replace("_", " ");
    return s.charAt(0).toUpperCase() + s.substring(1);
  }
  function formatDate(d) {
    const date = d instanceof Date ? d : new Date(d);
    return new Intl.DateTimeFormat("default", { dateStyle: "long", timeStyle: "short" }).format(date);
  }
  var $filters = {
    formatDate,
    formatText,
    pluralise
  };

  // js/release/main.ts
  var app = createApp(Release_default2);
  app.config.globalProperties.$filters = $filters;
  app.mount("#vue-app-release");
})();
/*! Bundled license information:

@vue/shared/dist/shared.esm-bundler.js:
  (**
  * @vue/shared v3.5.13
  * (c) 2018-present Yuxi (Evan) You and Vue contributors
  * @license MIT
  **)
  (*! #__NO_SIDE_EFFECTS__ *)

@vue/reactivity/dist/reactivity.esm-bundler.js:
  (**
  * @vue/reactivity v3.5.13
  * (c) 2018-present Yuxi (Evan) You and Vue contributors
  * @license MIT
  **)

@vue/runtime-core/dist/runtime-core.esm-bundler.js:
  (**
  * @vue/runtime-core v3.5.13
  * (c) 2018-present Yuxi (Evan) You and Vue contributors
  * @license MIT
  **)

@vue/runtime-core/dist/runtime-core.esm-bundler.js:
  (*! #__NO_SIDE_EFFECTS__ *)

@vue/runtime-core/dist/runtime-core.esm-bundler.js:
  (*! #__NO_SIDE_EFFECTS__ *)

@vue/runtime-core/dist/runtime-core.esm-bundler.js:
  (*! #__NO_SIDE_EFFECTS__ *)

@vue/runtime-dom/dist/runtime-dom.esm-bundler.js:
  (**
  * @vue/runtime-dom v3.5.13
  * (c) 2018-present Yuxi (Evan) You and Vue contributors
  * @license MIT
  **)

@vue/runtime-dom/dist/runtime-dom.esm-bundler.js:
  (*! #__NO_SIDE_EFFECTS__ *)

@vue/runtime-dom/dist/runtime-dom.esm-bundler.js:
  (*! #__NO_SIDE_EFFECTS__ *)

vue/dist/vue.runtime.esm-bundler.js:
  (**
  * vue v3.5.13
  * (c) 2018-present Yuxi (Evan) You and Vue contributors
  * @license MIT
  **)
*/
//# sourceMappingURL=release.js.map
