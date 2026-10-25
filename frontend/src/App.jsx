import BarraNavegacion, { MENU } from './componentes/BarraNavegacion'
import { Cargando } from './componentes/Estado'
import { useRuta } from './hooks/useRuta'
import { useSesion } from './hooks/useSesion'
import Dashboard from './paginas/Dashboard'
import FichaEstudiante from './paginas/ficha/FichaEstudiante'
import Importacion from './paginas/Importacion'
import ListaEstudiantes from './paginas/ListaEstudiantes'
import Login from './paginas/Login'
import MisCasos from './paginas/MisCasos'
import ReglasRiesgo from './paginas/ReglasRiesgo'

const PAGINAS = {
  dashboard: { componente: Dashboard, permiso: 'ver_dashboard' },
  estudiantes: { componente: ListaEstudiantes, permiso: 'ver_estudiantes' },
  estudiante: { componente: FichaEstudiante, permiso: 'ver_ficha' },
  casos: { componente: MisCasos, permiso: 'ver_seguimiento' },
  importar: { componente: Importacion, permiso: 'importar_datos' },
  reglas: { componente: ReglasRiesgo, permiso: 'configurar_reglas' },
}

export default function App() {
  const { usuario, verificando, puede } = useSesion()
  const { pagina, parametros } = useRuta()

  if (verificando) return <div className="container"><Cargando texto="Verificando sesión..." /></div>
  if (!usuario) return <Login />

  const inicio = MENU.find((m) => puede(m.permiso))?.pagina || 'estudiantes'
  const actual = PAGINAS[pagina] ? pagina : inicio
  const { componente: Pagina, permiso } = PAGINAS[actual]

  return (
    <>
      <BarraNavegacion pagina={actual} />
      <main className="container-fluid px-3 px-lg-4 pb-5">
        {permiso && !puede(permiso)
          ? <div className="alert alert-warning">Su rol no tiene acceso a esta sección.</div>
          : <Pagina parametros={parametros} />}
      </main>
    </>
  )
}
