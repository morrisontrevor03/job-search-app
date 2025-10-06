import { useAuth } from './AuthContext'

export default function UserProfile() {
  const { user, signOut } = useAuth()

  if (!user) return null

  return (
    <div className="user-profile">
      <div className="user-info">
        <span className="user-email">{user.email}</span>
        {user.user_metadata?.full_name && (
          <span className="user-name">({user.user_metadata.full_name})</span>
        )}
      </div>
      <button onClick={signOut} className="sign-out-button">
        Sign Out
      </button>
    </div>
  )
}
