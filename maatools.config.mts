import type { FullConfig } from '@nekosu/maa-tools'

const config: FullConfig = {
  cwd: import.meta.dirname,
  maaVersion: '5.12.1',
  // The production PI has multiple controller/resource combinations pointing to
  // the same bundle. Use a single-combination wrapper for deterministic checks.
  interfacePath: 'assets/interface.check.json',
  check: {
    override: {
      // 忽略 mpe-config 带来的报错
      // ignore warning caused by mpe-config
      // 'mpe-config': 'ignore'
    }
  }
}

export default config
