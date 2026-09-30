import React, { useState } from 'react';
import { MapPin, Navigation, Search, ExternalLink, Info, Loader2 } from 'lucide-react';
import { api } from '../../services/api';
import { StateView } from '../../components/common/StateView';
import { Badge } from '../../components/common/Badge';
import { useLanguage } from '../../context/LanguageContext';

interface NearestFacility {
  id: string;
  name: string;
  code: string;
  facility_type: string;
  state: string;
  district: string;
  latitude: number;
  longitude: number;
  straight_line_km: number;
  driving_distance_km?: number | null;
  driving_minutes?: number | null;
}

interface NearestResponse {
  origin_latitude: number;
  origin_longitude: number;
  origin_label?: string | null;
  method: 'google_routes' | 'haversine_only' | string;
  method_note: string;
  facilities: NearestFacility[];
}

type Failure = { status: number; message: string };

const mapsLink = (f: { latitude: number; longitude: number }) =>
  `https://www.google.com/maps/dir/?api=1&destination=${f.latitude},${f.longitude}`;

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '0.6rem',
  borderRadius: '8px',
  border: '1px solid var(--border-color)',
  fontSize: '0.9rem',
};

export default function NearestFacilities() {
  const { t } = useLanguage();
  const [address, setAddress] = useState('');
  const [locating, setLocating] = useState(false);
  const [loading, setLoading] = useState(false);
  const [geoMessage, setGeoMessage] = useState<string | null>(null);
  const [failure, setFailure] = useState<Failure | null>(null);
  const [result, setResult] = useState<NearestResponse | null>(null);
  const [lastBody, setLastBody] = useState<Record<string, unknown> | null>(null);

  const search = async (body: Record<string, unknown>) => {
    setLoading(true);
    setFailure(null);
    setLastBody(body);
    const res = await api.post<NearestResponse>('/google/maps/nearest-facilities', { limit: 5, ...body });
    setLoading(false);
    if (res.error) {
      setResult(null);
      setFailure({ status: res.error.status, message: res.error.detail });
    } else {
      setResult(res.data);
    }
  };

  const useMyLocation = () => {
    setGeoMessage(null);
    if (!('geolocation' in navigator)) {
      setGeoMessage(t('nearest.geo.unsupported', 'Your browser does not support location. Please type an address or pincode instead.'));
      return;
    }
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocating(false);
        void search({ latitude: pos.coords.latitude, longitude: pos.coords.longitude });
      },
      (err) => {
        setLocating(false);
        setGeoMessage(
          err.code === err.PERMISSION_DENIED
            ? t('nearest.geo.denied', 'Location permission was denied. You can still type an address or pincode below.')
            : t('nearest.geo.failed', 'We could not determine your location. Please type an address or pincode instead.'),
        );
      },
      { timeout: 15000, maximumAge: 60000 },
    );
  };

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const a = address.trim();
    if (a.length < 3) {
      setGeoMessage(t('nearest.address.short', 'Please enter at least 3 characters.'));
      return;
    }
    setGeoMessage(null);
    void search({ address: a });
  };

  const failureTitle =
    failure?.status === 404
      ? t('nearest.err.notfound', 'Address not found')
      : failure?.status === 503
        ? t('nearest.err.unconfigured', 'Address lookup is not available')
        : undefined;
  const failureMessage =
    failure?.status === 503
      ? t('nearest.err.unconfigured.msg', 'Address search needs Google Maps, which is not configured on this server. Use "Use my location" instead.')
      : failure?.message;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', maxWidth: '820px', margin: '0 auto', width: '100%' }}>
      <header>
        <h2 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.4rem' }}>
          <MapPin size={22} aria-hidden="true" /> {t('nearest.title', 'Find nearest health facility')}
        </h2>
        <p style={{ margin: '0.35rem 0 0', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          {t('nearest.subtitle', 'Share your location or enter an address to see the closest facilities.')}
        </p>
      </header>

      <section className="glass-card" style={{ padding: '1.25rem', borderRadius: '14px', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div>
          <button
            type="button"
            className="btn-primary"
            onClick={useMyLocation}
            disabled={locating || loading}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}
          >
            {locating ? <Loader2 size={16} className="animate-spin" aria-hidden="true" /> : <Navigation size={16} aria-hidden="true" />}
            {locating ? t('nearest.locating', 'Getting your location...') : t('nearest.use_location', 'Use my location')}
          </button>
          <p style={{ margin: '0.5rem 0 0', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            {t('nearest.geo.why', 'Your browser will ask permission. Your location is only used once, to rank facilities by distance, and is not stored.')}
          </p>
        </div>

        <form onSubmit={onSubmit} style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', alignItems: 'flex-end' }}>
          <div style={{ flex: '1 1 220px' }}>
            <label htmlFor="nearest-address" style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.25rem' }}>
              {t('nearest.address.label', 'Or type an address or pincode')}
            </label>
            <input
              id="nearest-address"
              type="text"
              value={address}
              maxLength={300}
              onChange={(e) => setAddress(e.target.value)}
              style={inputStyle}
              placeholder={t('nearest.address.placeholder', 'e.g. village, town or pincode')}
            />
          </div>
          <button
            type="submit"
            className="btn-secondary"
            disabled={loading || locating}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', padding: '0.6rem 1rem' }}
          >
            <Search size={16} aria-hidden="true" /> {t('nearest.search', 'Search')}
          </button>
        </form>

        {geoMessage && (
          <p role="alert" style={{ margin: 0, color: '#b45309', fontSize: '0.85rem' }}>
            {geoMessage}
          </p>
        )}
      </section>

      <div aria-live="polite">
        {loading && <StateView state="loading" message={t('nearest.loading', 'Finding nearby facilities...')} />}

        {!loading && failure && (
          <StateView
            state={failure.status === 0 ? 'offline' : 'error'}
            title={failureTitle}
            message={failureMessage}
            onRetry={lastBody ? () => void search(lastBody) : undefined}
          />
        )}

        {!loading && !failure && result && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div
              role="note"
              style={{
                display: 'flex',
                gap: '0.5rem',
                padding: '0.75rem 1rem',
                borderRadius: '10px',
                background: result.method === 'google_routes' ? 'rgba(16,185,129,0.1)' : 'rgba(245,158,11,0.12)',
                fontSize: '0.85rem',
              }}
            >
              <Info size={16} style={{ flexShrink: 0, marginTop: '0.15rem' }} aria-hidden="true" />
              <div>
                <strong>
                  {result.method === 'google_routes'
                    ? t('nearest.method.routes', 'Distance and driving time')
                    : t('nearest.method.straight', 'Straight-line distance only')}
                </strong>
                <div>{result.method_note}</div>
                {result.origin_label && (
                  <div style={{ color: 'var(--text-muted)' }}>
                    {t('nearest.from', 'Searching from')}: {result.origin_label}
                  </div>
                )}
              </div>
            </div>

            {result.facilities.length === 0 ? (
              <StateView
                state="empty"
                title={t('nearest.empty.title', 'No facilities found')}
                message={t('nearest.empty.msg', 'No facilities with a known location were found.')}
              />
            ) : (
              <ol style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {result.facilities.map((f, i) => (
                  <li
                    key={f.id}
                    className="glass-card"
                    style={{ padding: '1rem', borderRadius: '12px', display: 'flex', flexWrap: 'wrap', gap: '0.75rem', justifyContent: 'space-between', alignItems: 'center' }}
                  >
                    <div style={{ flex: '1 1 240px', minWidth: 0 }}>
                      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
                        <strong>
                          {i + 1}. {f.name}
                        </strong>
                        <Badge status={f.facility_type} size="sm" />
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        {f.district}, {f.state}
                      </div>
                      <div style={{ fontSize: '0.9rem', marginTop: '0.4rem' }}>
                        {f.straight_line_km.toFixed(1)} km {t('nearest.straight', 'straight-line')}
                        {f.driving_distance_km != null && f.driving_minutes != null && (
                          <>
                            {' '}
                            &middot; {f.driving_distance_km.toFixed(1)} km {t('nearest.by_road', 'by road')}, ~{Math.round(f.driving_minutes)}{' '}
                            {t('nearest.min', 'min drive')}
                          </>
                        )}
                      </div>
                    </div>
                    <a
                      href={mapsLink(f)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn-secondary"
                      aria-label={`${t('nearest.open_maps', 'Open in Google Maps')}: ${f.name}`}
                      style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', textDecoration: 'none', padding: '0.5rem 0.9rem' }}
                    >
                      <ExternalLink size={14} aria-hidden="true" /> {t('nearest.open_maps', 'Open in Google Maps')}
                    </a>
                  </li>
                ))}
              </ol>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
