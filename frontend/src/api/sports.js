import service from './index'

export const getSportsConfig = () => {
  return service.get('/api/sports/config')
}

export const planSportsGame = (data) => {
  return service.post('/api/sports/game/plan', data)
}

export const getSportsPlanStatus = (params) => {
  return service.get('/api/sports/game/plan/status', { params })
}

export const getSportsWorkspace = (workspaceId) => {
  return service.get(`/api/sports/game/${workspaceId}`)
}

export const listSportsWorkspaces = (limit = 12) => {
  return service.get('/api/sports/game/list', { params: { limit } })
}

export const saveSportsScenario = (data) => {
  return service.post('/api/sports/game/scenario', data)
}

export const startSportsSimulation = (data) => {
  return service.post('/api/sports/game/simulate', data)
}

export const getSportsSimulationStatus = (params) => {
  return service.get('/api/sports/game/simulate/status', { params })
}

export const getSportsEvents = (params) => {
  return service.get('/api/sports/game/events', { params })
}

export const generateSportsReport = (data) => {
  return service.post('/api/sports/game/report/generate', data)
}

export const getSportsReportStatus = (params) => {
  return service.get('/api/sports/game/report/status', { params })
}

export const getSportsReport = (params) => {
  return service.get('/api/sports/game/report', { params })
}

export const chatWithSportsPersona = (data) => {
  return service.post('/api/sports/game/chat', data)
}
