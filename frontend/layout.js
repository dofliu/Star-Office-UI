// DofLab Office UI - 布局与层级配置
// 所有坐标、depth、资源路径统一管理在这里
// 避免 magic numbers，降低改错风险

// 核心规则：
// - 透明资源（如办公桌）强制 .png，不透明优先 .webp
// - 层级：低 → sofa(10) → starWorking(900) → desk(1000) → flower(1100)

// === 場景定義 ===
const SCENES = {
  // 場景1：主辦公室（研究與開發）
  mainOffice: {
    name: '主辦公室',
    description: '研究與開發區域',
    background: 'office_bg_small',
    areas: {
      door:        { x: 640, y: 550 },
      writing:     { x: 320, y: 360 },
      researching: { x: 320, y: 360 },
      error:       { x: 1066, y: 180 },
      breakroom:   { x: 640, y: 360 }
    },
    furniture: {
      sofa: { x: 670, y: 144, origin: { x: 0, y: 0 }, depth: 10 },
      desk: { x: 218, y: 417, origin: { x: 0.5, y: 0.5 }, depth: 1000 },
      flower: { x: 310, y: 390, origin: { x: 0.5, y: 0.5 }, depth: 1100, scale: 0.8 },
      starWorking: { x: 217, y: 333, origin: { x: 0.5, y: 0.5 }, depth: 900, scale: 1.32 },
      coffeeMachine: { x: 659, y: 397, origin: { x: 0.5, y: 0.5 }, depth: 99 },
      serverroom: { x: 1021, y: 142, origin: { x: 0.5, y: 0.5 }, depth: 2 },
      errorBug: { x: 1007, y: 221, origin: { x: 0.5, y: 0.5 }, depth: 50, scale: 0.9 },
      syncAnim: { x: 1157, y: 592, origin: { x: 0.5, y: 0.5 }, depth: 40 },
      cat: { x: 94, y: 557, origin: { x: 0.5, y: 0.5 }, depth: 2000 }
    }
  },
  
  // 場景2：創意工作室（設計與規劃）
  creativeStudio: {
    name: '創意工作室',
    description: '設計與規劃區域',
    background: 'office_bg_small',
    areas: {
      door:        { x: 640, y: 550 },
      writing:     { x: 500, y: 360 },
      researching: { x: 500, y: 360 },
      error:       { x: 1066, y: 180 },
      breakroom:   { x: 800, y: 360 }
    },
    furniture: {
      sofa: { x: 800, y: 144, origin: { x: 0, y: 0 }, depth: 10 },
      desk: { x: 400, y: 417, origin: { x: 0.5, y: 0.5 }, depth: 1000 },
      flower: { x: 500, y: 390, origin: { x: 0.5, y: 0.5 }, depth: 1100, scale: 0.8 },
      starWorking: { x: 400, y: 333, origin: { x: 0.5, y: 0.5 }, depth: 900, scale: 1.32 },
      coffeeMachine: { x: 900, y: 397, origin: { x: 0.5, y: 0.5 }, depth: 99 },
      serverroom: { x: 1100, y: 142, origin: { x: 0.5, y: 0.5 }, depth: 2 },
      errorBug: { x: 1007, y: 221, origin: { x: 0.5, y: 0.5 }, depth: 50, scale: 0.9 },
      syncAnim: { x: 1157, y: 592, origin: { x: 0.5, y: 0.5 }, depth: 40 },
      cat: { x: 200, y: 557, origin: { x: 0.5, y: 0.5 }, depth: 2000 }
    }
  },
  
  // 場景3：會議室（討論與協作）
  meetingRoom: {
    name: '會議室',
    description: '討論與協作區域',
    background: 'office_bg_small',
    areas: {
      door:        { x: 640, y: 550 },
      writing:     { x: 640, y: 360 },
      researching: { x: 640, y: 360 },
      error:       { x: 1066, y: 180 },
      breakroom:   { x: 400, y: 360 }
    },
    furniture: {
      sofa: { x: 400, y: 144, origin: { x: 0, y: 0 }, depth: 10 },
      desk: { x: 640, y: 417, origin: { x: 0.5, y: 0.5 }, depth: 1000 },
      flower: { x: 700, y: 390, origin: { x: 0.5, y: 0.5 }, depth: 1100, scale: 0.8 },
      starWorking: { x: 640, y: 333, origin: { x: 0.5, y: 0.5 }, depth: 900, scale: 1.32 },
      coffeeMachine: { x: 300, y: 397, origin: { x: 0.5, y: 0.5 }, depth: 99 },
      serverroom: { x: 900, y: 142, origin: { x: 0.5, y: 0.5 }, depth: 2 },
      errorBug: { x: 1007, y: 221, origin: { x: 0.5, y: 0.5 }, depth: 50, scale: 0.9 },
      syncAnim: { x: 1157, y: 592, origin: { x: 0.5, y: 0.5 }, depth: 40 },
      cat: { x: 1000, y: 557, origin: { x: 0.5, y: 0.5 }, depth: 2000 }
    }
  }
};

// 當前場景
let currentScene = 'mainOffice';

// 獲取當前場景配置
function getCurrentScene() {
  return SCENES[currentScene];
}

// 切換場景
function switchScene(sceneId) {
  if (SCENES[sceneId]) {
    currentScene = sceneId;
    return true;
  }
  return false;
}

const LAYOUT = {
  // === 游戏画布 ===
  game: {
    width: 1280,
    height: 720
  },

  // === 各区域坐标 ===
  get areas() {
    return getCurrentScene().areas;
  },

  // === 装饰与家具：坐标 + 原点 + depth ===
  get furniture() {
    return getCurrentScene().furniture;
  },

  // === 牌匾 ===
  plaque: {
    x: 640,
    y: 720 - 36,
    width: 420,
    height: 44
  },

  // === 资源加载规则：哪些强制用 PNG（透明资源） ===
  forcePng: {
    desk_v2: true // 新办公桌必须透明，强制 PNG
  },

  // === 总资源数量（用于加载进度条） ===
  totalAssets: 15
};
