<template>
    <div className="profile-page">
        <div className="page-header">
            <h1 className="page-title">个人中心</h1>
            <p className="page-subtitle">管理你的账户信息和使用统计</p>
        </div>

        <div className="profile-content">
            <div className="user-info-card">
                <div className="user-avatar-section">
                    <el-avatar size="80">
                        <img
                                src="https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png"
                                alt="用户头像"
                        />
                    </el-avatar>
                    <div className="user-basic-info">
                        <div className="user-name">示例用户</div>
                        <div className="user-role">普通用户</div>
                        <el-button
                                size="small"
                                type="primary"
                                plain
                                style="margin-top: 8px"
                        >
                            编辑资料
                        </el-button>
                    </div>
                </div>
            </div>

            <div className="stats-cards">
                <div className="stat-card">
                    <div className="stat-value">128</div>
                    <div className="stat-label">总检测次数</div>
                </div>
                <div className="stat-card">
                    <div className="stat-value">892</div>
                    <div className="stat-label">累计检测目标</div>
                </div>
                <div className="stat-card">
                    <div className="stat-value">98.5%</div>
                    <div className="stat-label">检测成功率</div>
                </div>
                <div className="stat-card">
                    <div className="stat-value">12</div>
                    <div className="stat-label">使用天数</div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup></script>

<style scoped lang="scss">
.profile-page {
  width: 100%;

  .page-header {
    margin-bottom: 24px;

    .page-title {
      font-size: 24px;
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: 8px;
    }

    .page-subtitle {
      font-size: 14px;
      color: var(--text-secondary);
    }
  }

  .profile-content {
    display: flex;
    flex-direction: column;
    gap: 24px;

    .user-info-card {
      background-color: #ffffff;
      border-radius: 10px;
      padding: 24px;
      box-shadow: var(--card-shadow);

      .user-avatar-section {
        display: flex;
        align-items: center;

        .user-basic-info {
          margin-left: 24px;

          .user-name {
            font-size: 24px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 4px;
          }

          .user-role {
            font-size: 14px;
            color: var(--text-secondary);
          }
        }
      }
    }

    .stats-cards {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 24px;

      .stat-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 24px;
        text-align: center;
        box-shadow: var(--card-shadow);

        .stat-value {
          font-size: 32px;
          font-weight: 700;
          color: var(--primary-color);
          margin-bottom: 8px;
        }

        .stat-label {
          font-size: 14px;
          color: var(--text-secondary);
        }
      }
    }
  }
}
</style>