import { ref, onMounted, onUnmounted } from 'vue'
import { io } from 'socket.io-client'

const socket = ref(null)
const connected = ref(false)
const eventHandlers = new Map()

export function useWebSocket() {
  function connect() {
    if (socket.value?.connected) return

    const url = import.meta.env.DEV ? 'http://127.0.0.1:19000' : window.location.origin
    socket.value = io(url, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
    })

    socket.value.on('connect', () => {
      connected.value = true
    })

    socket.value.on('disconnect', () => {
      connected.value = false
    })

    socket.value.on('connected', () => {
      connected.value = true
    })
  }

  function on(event, handler) {
    if (!socket.value) connect()
    socket.value.on(event, handler)

    // Track for cleanup
    if (!eventHandlers.has(event)) {
      eventHandlers.set(event, [])
    }
    eventHandlers.get(event).push(handler)
  }

  function off(event, handler) {
    socket.value?.off(event, handler)
  }

  function disconnect() {
    socket.value?.disconnect()
    socket.value = null
    connected.value = false
  }

  return { socket, connected, connect, on, off, disconnect }
}
